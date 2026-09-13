"""Админка модуля книг: учитель добавляет издания сам, без программиста."""
from django.contrib import admin

from apps.books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "author", "price", "order_pub", "is_published")
    list_editable = ("order_pub", "is_published")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "author")
    prepopulated_fields = {}  # slug нет — адрес один на раздел
