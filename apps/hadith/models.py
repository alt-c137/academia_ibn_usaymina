"""Хадисы: коллекция текстов и «хадис дня» (см. services.py)."""
from django.db import models

from apps.core.models import TimeStampedModel


class Hadith(TimeStampedModel):
    text = models.TextField("Текст хадиса")
    source = models.CharField("Источник", max_length=200, blank=True,
                              help_text="Например: Сахих аль-Бухари, №13")
    narrator = models.CharField("Передатчик", max_length=200, blank=True)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Хадис"
        verbose_name_plural = "Хадисы"
        ordering = ("id",)

    def __str__(self):
        return self.text[:60]
