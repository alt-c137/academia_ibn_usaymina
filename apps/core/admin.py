"""Админка ядра: контакты сайта."""
from django.contrib import admin

from apps.core.models import SiteInfo


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ("site_name", "whatsapp", "telegram", "email")

    # Запрещаем создавать вторую запись и удалять единственную
    def has_add_permission(self, request):
        return not SiteInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
