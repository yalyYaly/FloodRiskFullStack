from django.shortcuts import render
from .models import FloodReport


def home(request):
    risk = None
    advice = None

    if request.method == "POST":
        rainfall = float(request.POST["rainfall"])
        river_level = float(request.POST["river_level"])
        area_type = request.POST["area_type"]

        if rainfall > 100 and river_level > 5:
            risk = "HIGH"
        elif rainfall > 50 or river_level > 3:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if area_type == "Low-lying" and risk == "LOW":
            risk = "MEDIUM"
        elif area_type == "Low-lying" and risk == "MEDIUM":
            risk = "HIGH"

        if risk == "HIGH":
            advice = "Move to a safer place and follow emergency instructions."
        elif risk == "MEDIUM":
            advice = "Be alert. Monitor local weather and river updates."
        else:
            advice = "Risk is low. Stay informed about weather conditions."

        FloodReport.objects.create(
            rainfall=rainfall,
            river_level=river_level,
            area_type=area_type,
            risk=risk
        )

    return render(request, "predictor/home.html", {
        "risk": risk,
        "advice": advice
    })
    
def history(request):
    reports = FloodReport.objects.order_by("-created_at")
    return render(request, "predictor/history.html", {
        "reports": reports
    })