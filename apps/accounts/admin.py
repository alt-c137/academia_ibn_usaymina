"""Админка: управление пользователями (только чтение для учителя, удаление — нет)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "phone", "is_staff",
                    "is_trusted", "date_joined")
    search_fields = ("email", "first_name", "last_name", "phone", "telegram")
    list_filter = ("is_staff", "is_active", "is_trusted", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личные данные", {"fields": ("first_name", "last_name", "phone", "telegram",
                                       "avatar")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser",
                                       "is_trusted", "groups")}),
        ("Блокировка", {"fields": ("banned_until", "ban_reason")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
