from django.urls import path

from apps.books import views

app_name = "books"

urlpatterns = [
    path("", views.BookListView.as_view(), name="index"),
]
