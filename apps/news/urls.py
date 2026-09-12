"""Адреса модуля news (подключён в config/urls.py)."""
from django.urls import path

from apps.news import views

app_name = "news"

urlpatterns = [
    path("news/", views.PostListView.as_view(), name="list"),
    path("news/<slug:slug>/", views.PostDetailView.as_view(), name="detail"),
    path("faqs/", views.FAQView.as_view(), name="faq"),
]
