"""Адреса модуля library (подключён в config/urls.py как /library/)."""
from django.urls import path

from apps.library import views

app_name = "library"

urlpatterns = [
    path("", views.LibraryView.as_view(), name="index"),
    path("category/<slug:slug>/", views.CategoryView.as_view(), name="category"),
    path("item/<int:pk>/", views.item_redirect_view, name="item"),
]
