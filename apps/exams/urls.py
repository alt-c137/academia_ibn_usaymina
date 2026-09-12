"""Адреса модуля exams (подключён в config/urls.py как /exams/)."""
from django.urls import path

from apps.exams import views

app_name = "exams"

urlpatterns = [
    path("<int:pk>/", views.ExamDetailView.as_view(), name="detail"),
    path("<int:pk>/start/", views.exam_start_view, name="start"),
    path("attempt/<int:pk>/", views.ExamTakeView.as_view(), name="take"),
    path("attempt/<int:pk>/result/", views.ExamResultView.as_view(), name="result"),
]
