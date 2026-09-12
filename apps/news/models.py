"""Новости платформы и часто задаваемые вопросы."""
from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel


class Post(TimeStampedModel):
    title = models.CharField("Заголовок", max_length=250)
    slug = models.SlugField("Адрес (латиницей)", max_length=270, unique=True)
    cover = models.ImageField("Обложка", upload_to="news/covers/", blank=True)
    excerpt = models.CharField("Краткий вводный текст", max_length=400, blank=True)
    body = models.TextField("Текст новости")
    published_at = models.DateTimeField("Дата публикации", null=True, blank=True,
                                        help_text="Пусто = не показывать на сайте")
    is_published = models.BooleanField("Опубликовано", default=False)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ("-published_at", "-created_at")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})


class FAQ(models.Model):
    question = models.CharField("Вопрос", max_length=300)
    answer = models.TextField("Ответ")
    order = models.PositiveSmallIntegerField("Порядок", default=1)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Вопрос-ответ"
        verbose_name_plural = "Вопросы-ответы (FAQ)"
        ordering = ("order", "pk")

    def __str__(self):
        return self.question
