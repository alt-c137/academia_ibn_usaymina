"""Админка модуля exams: тесты с вопросами, вопросы с вариантами, результаты."""
from django.contrib import admin

from apps.exams.models import Answer, Attempt, Choice, Exam, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ("order", "text", "q_type", "points")
    show_change_link = True  # переход к вопросу для заполнения вариантов


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ("order", "text", "is_correct")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "kind", "time_limit_min", "max_attempts",
                    "pass_percent", "is_published")
    list_filter = ("course", "kind", "is_published")
    search_fields = ("title",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("exam", "order", "text", "q_type", "points")
    list_filter = ("exam", "q_type")
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Результаты попыток — только просмотр (изменять нельзя)."""
    list_display = ("student", "exam", "started_at", "score_percent", "passed")
    list_filter = ("exam", "passed")
    search_fields = ("student__email",)
    readonly_fields = [f.name for f in Attempt._meta.fields]
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Answer)  # ответы видно внутри попытки; отдельно — без настроек
