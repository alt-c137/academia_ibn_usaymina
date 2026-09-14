"""Админка ядра: контакты сайта."""
from django.contrib import admin

from apps.core.models import SiteInfo


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ("site_name", "whatsapp", "telegram", "email")

    # Настройки разделов — отдельная группа полей, чтобы владелец видел
    # все включатели в одном месте
    fieldsets = (
        ("Контакты", {"fields": ("site_name", "tagline", "whatsapp", "telegram",
                                  "email", "about_footer")}),
        ("Разделы сайта", {"fields": ("forum_enabled", "hadith_enabled",
                                       "library_enabled", "show_books",
                                       "stories_enabled", "secular_courses_enabled")}),
        ("Реклама", {"fields": ("adsense_enabled", "adsense_client_id")}),
        ("Форум", {"fields": ("forum_comments_enabled",)}),
        ("Оплата и поддержка", {"fields": ("payment_details", "show_donations",
                                            "donations_title", "donations_text",
                                            "donations_details")}),
        ("Сдача через мессенджеры", {"fields": ("submissions_via_messengers",
                                                 "messengers_note")}),
    )

    # Запрещаем создавать вторую запись и удалять единственную
    def has_add_permission(self, request):
        return not SiteInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
