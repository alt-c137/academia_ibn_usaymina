"""Админка рекламы: слот → креативы внутри него (inline)."""
from django.contrib import admin

from apps.ads.models import AdCreative, AdSlot


class AdCreativeInline(admin.TabularInline):
    model = AdCreative
    extra = 0
    fields = ("advertiser_name", "image", "video", "audio", "link_url",
              "starts_at", "ends_at", "is_active")


@admin.register(AdSlot)
class AdSlotAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active")
    list_editable = ("is_active",)
    inlines = (AdCreativeInline,)

    # Слоты фиксированы кодом шаблонов: не даём плодить дубли мест
    def has_add_permission(self, request):
        return not AdSlot.objects.exists()
