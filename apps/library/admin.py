"""Админка библиотеки."""
from django.contrib import admin

from apps.library.models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "item_type", "views", "is_published")
    list_filter = ("category", "item_type", "is_published")
    list_editable = ("is_published",)
    search_fields = ("title", "description")
