from django.shortcuts import render
from .models import FloodReport
from .ml_model import predict_risk


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

        FloodReport.objects.create(
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
    
def history(request):
    reports = FloodReport.objects.order_by("-created_at")
    return render(request, "predictor/history.html", {
        "reports": reports
    })