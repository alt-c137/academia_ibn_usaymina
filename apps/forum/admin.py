"""Админка форума: разделы, темы, ответы — модерация в один клик."""
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
                    "is_closed", "views", "created_at")
    list_filter = ("board", "is_approved", "is_pinned", "is_closed")
    search_fields = ("title", "body", "author__email")
    list_editable = ("is_approved", "is_pinned", "is_closed")
    actions = ("approve",)

    @admin.action(description="Одобрить (опубликовать)")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Темы опубликованы.")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at")
    search_fields = ("body", "thread__title", "author__email")
