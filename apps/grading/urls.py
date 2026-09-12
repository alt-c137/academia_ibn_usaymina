"""Адреса модуля grading (подключён в config/urls.py как /office/)."""
from django.urls import path

from apps.grading import views

app_name = "grading"

urlpatterns = [
    path("", views.OfficeView.as_view(), name="office"),
    path("transcript/", views.TranscriptView.as_view(), name="transcript"),
]
