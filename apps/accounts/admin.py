"""
Админка пользователей.

РОЛИ ПРОЕКТА (группы создаются автоматически после migrate, см.
apps/accounts/apps.py → ensure_teacher_group; назначаются в админке
→ Пользователи → выбрать пользователя → Группы):

  «Учитель»            — курсы/уроки/экзамены/задания/оценки/библиотека/
                         новости/книги + учительская /teacher/.
  «Модератор форума»   — темы и ответы форума: одобрять, закреплять,
                         закрывать, удалять; очередь /forum/moderation/.
  «Редактор новостей»  — новости и FAQ без прочих прав.
  is_trusted           — не роль, а галочка: доверенное лицо, может
                         отвечать в темах «только учителя и доверенные».
  is_staff             — доступ к админке; is_superuser — всё.
"""
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
