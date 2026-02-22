from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "core"

urlpatterns = [
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forbidden/", views.forbidden_view, name="forbidden"),
]
