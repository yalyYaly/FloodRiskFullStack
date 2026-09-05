from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("history/", views.history, name="history"),
    path("chat/", views.chat, name="chat"),
    path("accounts/", views.account_dashboard, name="account_dashboard"),
    path("claim-admin/", views.claim_admin, name="claim_admin"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.signin, name="login"),
    path("logout/", views.signout, name="logout"),
]