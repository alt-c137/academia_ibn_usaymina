"""
Админка модуля assignments. Главный экран учителя для проверки —
«Ответы на задания»: фильтр по курсу, статусу; баллы и комментарий
проставляются прямо здесь.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.assignments.models import Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "week", "max_points", "due_at", "is_published")
    list_filter = ("course", "is_published")
    list_editable = ("is_published",)
    search_fields = ("title",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "score", "submitted_short",
                    "graded_at")
    list_filter = ("assignment__course", "status")
    search_fields = ("student__email", "student__first_name", "student__last_name")
    list_editable = ("score",)  # быстрое выставление баллов прямо в списке
    readonly_fields = ("assignment", "student", "text", "file", "created_at", "updated_at")
    list_per_page = 30

    @admin.display(description="Отправлено")
    def submitted_short(self, obj):
        return timezone.localtime(obj.updated_at).strftime("%d.%m.%Y %H:%M")

    def save_model(self, request, obj, form, change):
        """Когда учитель ставит балл — фиксируем кто и когда проверил."""
        if obj.score is not None:
            obj.status = Submission.Status.GRADED
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False  # ответы создают студенты, а не админ
