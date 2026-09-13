from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("", views.MyInvoicesView.as_view(), name="my"),
]
