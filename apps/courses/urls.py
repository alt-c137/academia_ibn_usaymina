"""Адреса модуля courses (подключён в config/urls.py как /courses/)."""
from django.urls import path

from apps.courses import views

app_name = "courses"

urlpatterns = [
    path("", views.CourseListView.as_view(), name="list"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="detail"),
    path("<slug:slug>/enroll/", views.enroll_view, name="enroll"),
    path("<slug:course_slug>/<int:number>/", views.LessonDetailView.as_view(), name="lesson"),
    path(
        "<slug:course_slug>/<int:number>/complete/",
        views.lesson_complete_view,
        name="lesson_complete",
    ),
]
