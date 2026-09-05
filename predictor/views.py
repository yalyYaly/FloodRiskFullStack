from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import LoginForm, SignUpForm
from .models import FloodReport
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
    })
    
@login_required
def history(request):
    reports = FloodReport.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "predictor/history.html", {
        "reports": reports
    })


@login_required
def signout(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")