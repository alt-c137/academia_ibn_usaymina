"""
Книги платформы — раздел продажи печатных изданий учителя.

Модуль отключаемый: чтобы раздел исчез с сайта, достаточно убрать
«apps.books» из INSTALLED_APPS и строку в config/urls.py (см. README),
а чтобы просто временно спрятать — выключить переключатель
«Показывать раздел книг» в админке (Контакты сайта).
"""
from django.db import models

from apps.core.models import TimeStampedModel


class Book(TimeStampedModel):
    class Kind(models.TextChoices):
        FREE = "free", "Бесплатные (скачать)"
        ONLINE = "online", "Онлайн-книги (читать)"
        PAID = "paid", "Продаются"

    kind = models.CharField(
        "Раздел", max_length=10, choices=Kind.choices, default=Kind.PAID,
        help_text="Бесплатные и онлайн-книги открываются по ссылке «Читать»",
    )
    title = models.CharField("Название", max_length=200)
    author = models.CharField("Автор", max_length=160, blank=True)
    description = models.TextField("Описание", blank=True)
    cover = models.ImageField("Обложка", upload_to="books/covers/", blank=True)
    # Цена — надписью, а не числом: админ пишет «45 000 сум» или «бесплатно».
    price = models.CharField("Цена (надпись)", max_length=60, blank=True)
    # Ссылка чтения для бесплатных/онлайн-книг (PDF, читальня, облако).
    read_url = models.URLField("Ссылка на чтение/скачивание", blank=True)
    # Куда ведёт кнопка «Заказать»: внешний магазин, пост в Telegram и т.п.
    # Пусто — кнопка откроет чат WhatsApp из контактов сайта.
    order_url = models.URLField("Ссылка для заказа (магазин/пост)", blank=True)
    order_note = models.CharField("Подпись к кнопке", max_length=80, blank=True,
                                  default="Заказать")
    order_pub = models.PositiveSmallIntegerField("Порядок вывода", default=1)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ("order_pub", "pk")

    def __str__(self):
        return self.title
