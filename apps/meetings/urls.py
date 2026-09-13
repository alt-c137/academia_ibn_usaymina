"""Адреса модуля meetings (подключён в config/urls.py как /meetings/)."""
from django.urls import path

from apps.meetings import views

app_name = "meetings"

urlpatterns = [
    path("", views.MeetingListView.as_view(), name="list"),
]
