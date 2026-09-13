"""Админка онлайн-встреч."""
from django.contrib import admin

from apps.meetings.models import Meeting


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "starts_at", "duration_min", "is_published")
    list_filter = ("course", "is_published")
    list_editable = ("is_published",)
    search_fields = ("title", "description")
    date_hierarchy = "starts_at"
