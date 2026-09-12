"""
Библиотека материалов — как раздел «Библиотека» на hdat.sa:
категории (хадисы, акыда, фикх…) с числом файлов, счётчик просмотров.
"""
from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField("Название категории", max_length=120)
    slug = models.SlugField("Адрес (латиницей)", max_length=140, unique=True)
    order = models.PositiveSmallIntegerField("Порядок", default=1)

    class Meta:
        verbose_name = "Категория библиотеки"
        verbose_name_plural = "Категории библиотеки"
        ordering = ("order", "pk")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("library:category", kwargs={"slug": self.slug})

    def published_count(self) -> int:
        return self.items.filter(is_published=True).count()


class Item(TimeStampedModel):
    class Type(models.TextChoices):
        PDF = "pdf", "PDF-файл"
        AUDIO = "audio", "Аудио"
        VIDEO = "video", "Видео"
        LINK = "link", "Ссылка"

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="items", verbose_name="Категория"
    )
    title = models.CharField("Название", max_length=250)
    description = models.TextField("Описание", blank=True)
    item_type = models.CharField("Тип материала", max_length=10, choices=Type.choices,
                                 default=Type.PDF)
    file = models.FileField("Файл", upload_to="library/%Y/", blank=True)
    url = models.URLField("Внешняя ссылка", blank=True)
    views = models.PositiveIntegerField("Просмотров", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("library:item", kwargs={"pk": self.pk})
