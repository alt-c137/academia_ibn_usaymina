"""Админка форума: модерация тем, выборочное закрытие комментариев."""
from django.contrib import admin

from apps.forum.models import Board, Post, Thread


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_published")
    list_editable = ("order", "is_published")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "board", "author", "is_approved", "is_pinned",
                    "allow_comments", "visibility", "who_can_answer", "views")
    list_filter = ("board", "is_approved", "is_pinned", "is_closed",
                   "allow_comments", "visibility", "who_can_answer")
    search_fields = ("title", "body", "author__email")
    list_editable = ("is_approved", "is_pinned", "allow_comments")
    actions = ("approve", "comments_off", "comments_on", "make_private", "make_public")

    @admin.action(description="Одобрить (опубликовать)")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Темы опубликованы.")

    @admin.action(description="Закрыть комментарии у выбранных тем")
    def comments_off(self, request, queryset):
        count = queryset.update(allow_comments=False)
        self.message_user(request, f"Комментарии закрыты в темах: {count}. "
                                   "(Глобальный выключатель — «Контакты сайта»)")

    @admin.action(description="Открыть комментарии у выбранных тем")
    def comments_on(self, request, queryset):
        count = queryset.update(allow_comments=True)
        self.message_user(request, f"Комментарии открыты в темах: {count}.")

    @admin.action(description="Сделать приватными (видно учителям)")
    def make_private(self, request, queryset):
        queryset.update(visibility=Thread.Visibility.TEACHERS_ONLY)
        self.message_user(request, "Темы стали приватными.")

    @admin.action(description="Сделать публичными (видно всем)")
    def make_public(self, request, queryset):
        queryset.update(visibility=Thread.Visibility.PUBLIC)
        self.message_user(request, "Темы стали публичными.")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "is_official", "created_at")
    list_filter = ("is_official",)
    search_fields = ("body", "thread__title", "author__email")
    list_editable = ("is_official",)
