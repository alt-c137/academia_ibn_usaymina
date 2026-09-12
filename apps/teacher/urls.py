"""Адреса учительской (подключён в config/urls.py как /teacher/)."""
from django.urls import path

from apps.teacher import views

app_name = "teacher"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("submissions/", views.SubmissionListView.as_view(), name="submissions"),
    path("submissions/<int:pk>/", views.SubmissionDetailView.as_view(), name="submission"),
    path("attempts/", views.AttemptListView.as_view(), name="attempts"),
    path("attempts/<int:pk>/", views.AttemptDetailView.as_view(), name="attempt"),
]
