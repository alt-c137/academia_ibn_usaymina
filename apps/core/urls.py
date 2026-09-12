"""Адреса модуля core: главная страница, контакты, robots.txt."""
from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("contact/", views.contact_view, name="contact"),
    path("robots.txt", views.robots_view, name="robots"),
]
