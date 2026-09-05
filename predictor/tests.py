from django.test import TestCase

from .ml_model import predict_risk
from .models import FloodReport


class RiskPredictionTests(TestCase):
	def test_uses_rule_fallback_without_enough_training_data(self):
		risk, method = predict_risk(75, 2, "Normal")

		self.assertEqual(risk, "MEDIUM")
		self.assertIn("fallback", method)

	def test_uses_random_forest_with_all_risk_classes(self):
		FloodReport.objects.bulk_create([
			FloodReport(rainfall=10, river_level=1, area_type="Normal", risk="LOW"),
			FloodReport(rainfall=20, river_level=1.5, area_type="Hilly", risk="LOW"),
			FloodReport(rainfall=75, river_level=2, area_type="Normal", risk="MEDIUM"),
			FloodReport(rainfall=80, river_level=3.5, area_type="Hilly", risk="MEDIUM"),
			FloodReport(rainfall=120, river_level=6, area_type="Normal", risk="HIGH"),
			FloodReport(rainfall=140, river_level=7, area_type="Low-lying", risk="HIGH"),
		])

		risk, method = predict_risk(120, 6, "Normal")

		self.assertEqual(risk, "HIGH")
		self.assertEqual(method, "Random Forest")
