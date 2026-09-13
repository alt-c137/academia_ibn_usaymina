"""Свои счета студенту: «Мои платежи» (страница + блок для кабинета)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView

from apps.payments.models import Invoice


class MyInvoicesView(LoginRequiredMixin, ListView):
    template_name = "payments/my_invoices.html"
    context_object_name = "invoices"
    paginate_by = 20

    def get_queryset(self):
        return (
            Invoice.objects.filter(student=self.request.user, is_active=True)
            .prefetch_related("installments")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context
