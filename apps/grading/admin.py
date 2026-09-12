"""Админка модуля grading: посещаемость встреч и выданные выписки."""
from django.contrib import admin

from apps.grading.models import Attendance, Transcript


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "date", "present")
    list_filter = ("present", "enrollment__course")
    search_fields = ("enrollment__student__email", "enrollment__student__first_name")
    date_hierarchy = "date"


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    """Выписки — только просмотр: документ выдан, менять нельзя."""
    list_display = ("code", "student_name", "course_title", "total_points", "passed",
                    "created_at")
    list_filter = ("passed",)
    search_fields = ("code", "student_name")
    readonly_fields = [f.name for f in Transcript._meta.fields]
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
