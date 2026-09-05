from django.contrib.auth import login, logout
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .forms import LoginForm, SignUpForm
from .models import ChatMessage, Conversation, DeletedAccount, FloodReport
from .ml_model import predict_risk


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})


def signin(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "home")
    return render(request, "registration/login.html", {"form": form})


def home(request):
    risk = None
    advice = None
    prediction_method = None
    flood_facts = {
        "weather_share": "35-40%",
        "exposed_people": "35.1 million",
        "annual_losses": "USD 388.4 billion",
        "future_losses": "USD 407-439 billion by 2050",
    }

    if request.method == "POST":
        rainfall = float(request.POST["rainfall"])
        river_level = float(request.POST["river_level"])
        area_type = request.POST["area_type"]

        risk, prediction_method = predict_risk(rainfall, river_level, area_type)

        if risk == "HIGH":
            advice = "Move to a safer place and follow emergency instructions."
        elif risk == "MEDIUM":
            advice = "Be alert. Monitor local weather and river updates."
        else:
            advice = "Risk is low. Stay informed about weather conditions."

        if request.user.is_authenticated:
            FloodReport.objects.create(
                user=request.user,
                rainfall=rainfall,
                river_level=river_level,
                area_type=area_type,
                risk=risk
            )

    return render(request, "predictor/home.html", {
        "risk": risk,
        "advice": advice,
        "prediction_method": prediction_method,
        "flood_facts": flood_facts,
        "can_claim_admin": request.user.is_authenticated and settings.DEBUG and not User.objects.filter(is_superuser=True).exists(),
    })


def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /accounts/\n"
        f"Disallow: /chat/\nDisallow: /history/\nSitemap: {sitemap_url}\n",
        content_type="text/plain",
    )


def sitemap_xml(request):
    public_paths = ("/", "/login/", "/signup/")
    urls = "".join(
        f"<url><loc>{request.build_absolute_uri(path)}</loc></url>"
        for path in public_paths
    )
    return HttpResponse(
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        content_type="application/xml",
    )
    
@login_required
def history(request):
    reports = FloodReport.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "predictor/history.html", {
        "reports": reports
    })


def build_assistant_reply(prompt, user):
    prompt = prompt.lower()
    latest_report = FloodReport.objects.filter(user=user).order_by("-created_at").first()

    if any(word in prompt for word in ("emergency", "danger", "help", "trapped")):
        return (
            "If there is immediate danger, move to higher ground if you can do so safely, "
            "call your local emergency service, and follow official evacuation instructions. "
            "I cannot see live conditions or replace emergency responders."
        )

    if "history" in prompt or "report" in prompt:
        if latest_report:
            return (
                f"Your latest saved report is {latest_report.risk} risk with "
                f"{latest_report.rainfall:g} mm rainfall and a "
                f"{latest_report.river_level:g} m river level. "
                "Open Report History for the full list."
            )
        return "You do not have any saved flood reports yet. Run a prediction while signed in to create one."

    if any(word in prompt for word in ("risk", "rain", "river", "predict")):
        if latest_report:
            return (
                f"Your latest saved prediction is {latest_report.risk} risk. "
                f"It used {latest_report.rainfall:g} mm rainfall, "
                f"a {latest_report.river_level:g} m river level, and a "
                f"{latest_report.area_type.lower()} area type. "
                "For a new result, use the prediction form on the home page."
            )
        return "Enter rainfall, river level, and area type on the home page to create a flood-risk prediction."

    return (
        "I am your personal flood assistant. Ask me about your saved risk reports, "
        "flood preparation, or how to use the prediction form. For live warnings, "
        "always check your local emergency authority."
    )


@login_required
def chat(request):
    conversation, _ = Conversation.objects.get_or_create(user=request.user)
    error = None

    if request.method == "POST":
        prompt = request.POST.get("message", "").strip()
        if not prompt:
            error = "Write a message before sending it."
        elif len(prompt) > 2000:
            error = "Messages must be 2,000 characters or fewer."
        else:
            ChatMessage.objects.create(
                conversation=conversation,
                role="user",
                content=prompt,
            )
            ChatMessage.objects.create(
                conversation=conversation,
                role="assistant",
                content=build_assistant_reply(prompt, request.user),
            )
            return redirect("chat")

    return render(request, "predictor/chat.html", {
        "conversation": conversation,
        "messages": conversation.messages.all(),
        "error": error,
    })


User = get_user_model()


def staff_required(view):
    return user_passes_test(lambda user: user.is_authenticated and user.is_staff)(view)


@staff_required
def account_dashboard(request):
    error = None
    search_query = request.GET.get("q", "").strip()
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        target_user = User.objects.filter(pk=user_id).first()
        if target_user is None:
            error = "That account no longer exists."
        elif target_user.pk == request.user.pk or target_user.is_superuser:
            error = "Your administrator account cannot be deleted."
        else:
            DeletedAccount.objects.create(
                username=target_user.get_username(),
                email=target_user.email,
                deleted_by=request.user,
            )
            target_user.delete()
            return redirect("account_dashboard")

    accounts = User.objects.order_by("date_joined")
    if search_query:
        accounts = accounts.filter(
            Q(first_name__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    return render(request, "predictor/account_dashboard.html", {
        "accounts": accounts,
        "deleted_accounts": DeletedAccount.objects.all(),
        "deleted_count": DeletedAccount.objects.count(),
        "error": error,
        "search_query": search_query,
    })


@login_required
def claim_admin(request):
    if request.method == "POST" and settings.DEBUG and not User.objects.filter(is_superuser=True).exists():
        request.user.is_staff = True
        request.user.is_superuser = True
        request.user.save(update_fields=["is_staff", "is_superuser"])
        return redirect("account_dashboard")
    return redirect("home")


@login_required
def signout(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")