from sklearn.ensemble import RandomForestClassifier

from .models import FloodReport


MIN_TRAINING_SAMPLES = 6
AREA_CODES = {
    "Normal": 0,
    "Low-lying": 1,
    "Hilly": 2,
}


def _features(rainfall, river_level, area_type):
    return [[rainfall, river_level, AREA_CODES.get(area_type, 0)]]


def _rule_based_risk(rainfall, river_level, area_type):
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

    return risk


def predict_risk(rainfall, river_level, area_type):
    reports = list(FloodReport.objects.values("rainfall", "river_level", "area_type", "risk"))
    labels = [report["risk"] for report in reports]
    has_training_data = (
        len(reports) >= MIN_TRAINING_SAMPLES
        and len(set(labels)) == 3
    )

    if has_training_data:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        training_features = [
            _features(report["rainfall"], report["river_level"], report["area_type"])[0]
            for report in reports
        ]
        model.fit(training_features, labels)
        risk = model.predict(_features(rainfall, river_level, area_type))[0]
        return risk, "Random Forest"

    return _rule_based_risk(rainfall, river_level, area_type), "Rule-based fallback (more labeled data required)"