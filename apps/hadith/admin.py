"""Админка хадисов: учитель добавляет тексты, публикация галочкой."""
from django.contrib import admin

from apps.hadith.models import Hadith


@admin.register(Hadith)
class HadithAdmin(admin.ModelAdmin):
    list_display = ("text", "narrator", "source", "is_published")
    list_editable = ("is_published",)
    list_filter = ("is_published",)
    search_fields = ("text", "narrator", "source")
