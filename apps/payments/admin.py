"""Админка оплат: учитель выставляет счета, размечает график и поступления."""
from django.contrib import admin
from django.utils import timezone

from apps.payments.models import Installment, Invoice


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    fields = ("number", "amount", "due_at", "is_paid", "paid_at", "method")
    readonly_fields = ()


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "get_kind", "total", "paid_total",
                    "percent", "is_active", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("student__email", "student__first_name", "student__last_name", "title")
    inlines = (InstallmentInline,)
    actions = ("make_schedule_2", "make_schedule_3", "make_schedule_4")

    @admin.display(description="Тип")
    def get_kind(self, obj):
        return obj.get_kind_display()

    @admin.action(description="Разбить на 2 части (рассрочка)")
    def make_schedule_2(self, request, queryset):
        for invoice in queryset:
            invoice.create_schedule(2)
        self.message_user(request, "График на 2 части создан.")

    @admin.action(description="Разбить на 3 части (рассрочка)")
    def make_schedule_3(self, request, queryset):
        for invoice in queryset:
            invoice.create_schedule(3)
        self.message_user(request, "График на 3 части создан.")

    @admin.action(description="Разбить на 4 части (рассрочка)")
    def make_schedule_4(self, request, queryset):
        for invoice in queryset:
            invoice.create_schedule(4)
        self.message_user(request, "График на 4 части создан.")


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "number", "amount", "due_at", "is_paid", "paid_at")
    list_filter = ("is_paid",)
    search_fields = ("invoice__student__email", "invoice__title")
    actions = ("mark_paid",)

    @admin.action(description="Отметить поступившим (оплачено сейчас)")
    def mark_paid(self, request, queryset):
        queryset.update(is_paid=True, paid_at=timezone.now())
        self.message_user(request, "Отмечено оплаченным.")
