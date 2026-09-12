"""Адреса модуля assignments (подключён в config/urls.py как /assignments/)."""
from django.urls import path

from apps.assignments import views

app_name = "assignments"

urlpatterns = [
    path("<int:pk>/", views.AssignmentDetailView.as_view(), name="detail"),
]
