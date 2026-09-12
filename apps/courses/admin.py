"""Админка модуля courses: учитель ведёт программы, курсы и уроки здесь."""
from django.contrib import admin

from apps.courses.models import Course, Enrollment, Lesson, LessonProgress, Program


class LessonInline(admin.TabularInline):
    """Уроки редактируются прямо на странице курса."""
    model = Lesson
    extra = 1
    fields = ("order", "week", "title", "summary", "video_url", "document", "audio", "is_published")
    show_change_link = True


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_published")
    list_editable = ("order", "is_published")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "program", "status", "order", "is_published", "registration_open")
    list_filter = ("program", "status", "is_published")
    list_editable = ("status", "order", "is_published")
    search_fields = ("title", "book", "author")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]
    date_hierarchy = "start_date"

    @admin.display(boolean=True, description="Регистрация открыта")
    def registration_open(self, obj):
        return obj.registration_open


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "week", "title", "is_published")
    list_filter = ("course", "is_published")
    search_fields = ("title", "summary")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "created_at")
    list_filter = ("status", "course")
    search_fields = ("student__email", "student__first_name", "student__last_name")
    autocomplete_fields = ("student",)  # удобный поиск студента при большом их количестве


admin.site.register(LessonProgress)  # служебная таблица — без настроек
