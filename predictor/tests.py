from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase

from .ml_model import predict_risk
from .models import ChatMessage, Conversation, FloodReport


User = get_user_model()


class AuthenticationTests(TestCase):
	def test_signup_creates_and_logs_in_user(self):
		response = self.client.post("/signup/", {
			"first_name": "Asha",
			"username": "asha",
			"email": "asha@example.com",
			"password1": "StrongPassword123!",
			"password2": "StrongPassword123!",
		})

		self.assertRedirects(response, "/")
		self.assertTrue(response.wsgi_request.user.is_authenticated)
		self.assertTrue(User.objects.filter(username="asha").exists())

	def test_login_accepts_email_and_password_reset_sends_email(self):
		user = User.objects.create_user(
			username="asha",
			email="asha@example.com",
			password="StrongPassword123!",
		)

		login_response = self.client.post("/login/", {
			"identifier": "asha@example.com",
			"password": "StrongPassword123!",
		})
		self.assertRedirects(login_response, "/")

		self.client.post("/logout/")
		reset_response = self.client.post("/password-reset/", {"email": user.email})
		self.assertRedirects(reset_response, "/password-reset/done/")
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("Reset your Flood Risk Prediction password", mail.outbox[0].subject)


class ReportPrivacyTests(TestCase):
	def test_anonymous_users_can_check_risk_without_saving_a_report(self):
		response = self.client.post("/", {
			"rainfall": "75",
			"river_level": "2",
			"area_type": "Normal",
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Flood Risk: MEDIUM")
		self.assertEqual(FloodReport.objects.count(), 0)

	def test_report_history_is_private_to_each_user(self):
		first_user = User.objects.create_user(username="first", password="StrongPassword123!")
		second_user = User.objects.create_user(username="second", password="StrongPassword123!")

		self.client.force_login(first_user)
		self.client.post("/", {"rainfall": "75", "river_level": "2", "area_type": "Normal"})
		self.client.force_login(second_user)
		self.client.post("/", {"rainfall": "120", "river_level": "6", "area_type": "Normal"})

		first_user_reports = FloodReport.objects.filter(user=first_user)
		second_user_reports = FloodReport.objects.filter(user=second_user)
		self.assertEqual(first_user_reports.count(), 1)
		self.assertEqual(second_user_reports.count(), 1)

		response = self.client.get("/history/")
		self.assertContains(response, "120.0 mm")
		self.assertNotContains(response, "75.0 mm")


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


class ChatPrivacyTests(TestCase):
	def test_chat_requires_login(self):
		response = self.client.get("/chat/")

		self.assertRedirects(response, "/login/?next=/chat/")

	def test_chat_persists_messages_for_the_logged_in_user(self):
		user = User.objects.create_user(username="asha", password="StrongPassword123!")
		self.client.force_login(user)

		response = self.client.post("/chat/", {"message": "What is my risk?"})

		self.assertRedirects(response, "/chat/")
		conversation = Conversation.objects.get(user=user)
		self.assertEqual(conversation.messages.count(), 2)
		self.assertEqual(ChatMessage.objects.filter(role="assistant").count(), 1)
		self.assertContains(self.client.get("/chat/"), "Enter rainfall, river level, and area type")

	def test_chat_history_is_private_to_each_user(self):
		first_user = User.objects.create_user(username="first", password="StrongPassword123!")
		second_user = User.objects.create_user(username="second", password="StrongPassword123!")

		self.client.force_login(first_user)
		self.client.post("/chat/", {"message": "A private question"})
		self.client.force_login(second_user)

		response = self.client.get("/chat/")

		self.assertNotContains(response, "A private question")
		self.assertContains(response, "Hello second")


class AccountDashboardTests(TestCase):
	def test_staff_can_search_accounts_by_email_or_username(self):
		admin = User.objects.create_user(username="admin", password="StrongPassword123!", is_staff=True)
		User.objects.create_user(username="riverwatch", email="river@example.com", password="StrongPassword123!")
		User.objects.create_user(username="mountain", email="mountain@example.com", password="StrongPassword123!")
		self.client.force_login(admin)

		response = self.client.get("/accounts/?q=river@example.com")

		self.assertContains(response, "riverwatch")
		self.assertNotContains(response, "mountain")

	def test_non_staff_cannot_open_account_dashboard(self):
		user = User.objects.create_user(username="member", password="StrongPassword123!")
		self.client.force_login(user)

		response = self.client.get("/accounts/")

		self.assertEqual(response.status_code, 302)


class SearchVisibilityTests(TestCase):
	def test_public_seo_endpoints_and_home_metadata(self):
		robots_response = self.client.get("/robots.txt")
		sitemap_response = self.client.get("/sitemap.xml")
		home_response = self.client.get("/")

		self.assertContains(robots_response, "Sitemap: http://testserver/sitemap.xml")
		self.assertContains(sitemap_response, "http://testserver/")
		self.assertContains(home_response, "AI Flood Risk Prediction System")
		self.assertContains(home_response, "name=\"description\"")
