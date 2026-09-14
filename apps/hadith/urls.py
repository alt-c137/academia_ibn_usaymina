from django.urls import path

from apps.hadith import views

app_name = "hadith"

urlpatterns = [
    path("", views.HadithListView.as_view(), name="list"),
]
