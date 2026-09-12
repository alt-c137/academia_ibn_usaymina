"""
Общие модели ядра.

TimeStampedModel — абстрактный родитель: добавляет любому объекту поля
created_at / updated_at (когда создан и когда последний раз изменён).
SiteInfo — единственная на сайт запись с контактами и текстами (правится
в админке, чтобы учитель мог менять телефон WhatsApp без помощи программиста).
"""
from django.core.cache import cache
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        abstract = True  # таблицы в БД для этого класса не создаётся


class SiteInfo(models.Model):
    """Единственная запись с контактами платформы. Создаётся командой seed_demo
    или вручную: админка → Ядро платформы → Контакты сайта → Добавить."""

    site_name = models.CharField("Название платформы", max_length=120)
    tagline = models.CharField("Краткий слоган", max_length=200, blank=True)
    whatsapp = models.CharField("WhatsApp (номер с кодом страны, без +)", max_length=20, blank=True)
    telegram = models.CharField("Telegram (имя канала или @пользователя)", max_length=60, blank=True)
    email = models.EmailField("Электронная почта", blank=True)
    about_footer = models.TextField("Текст в подвале сайта", blank=True)

    # Отправка решений через мессенджеры — резервный канал на случай,
    # когда сайт недоступен. Включает и выключает учитель/админ.
    submissions_via_messengers = models.BooleanField(
        "Показывать на заданиях отправку через WhatsApp/Telegram", default=False,
        help_text="Резервный способ сдачи решений, если сайт недоступен",
    )
    messengers_note = models.CharField(
        "Пояснение к мессенджерам", max_length=300, blank=True,
        default="Если сайт недоступен — отправьте решение учителю в мессенджер, приложив файл:",
    )

    class Meta:
        verbose_name = "Контакты сайта"
        verbose_name_plural = "Контакты сайта"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ожидаем только одну запись; id всегда = 1.
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_info")

    @classmethod
    def load(cls) -> "SiteInfo | None":
        """Возвращает запись контактов (с кэшем на 1 час, чтобы не дёргать БД каждый запрос)."""
        info = cache.get("site_info")
        if info is None and not SiteInfo.objects.exists():
            return None
        if info is None:
            info = SiteInfo.objects.first()
            cache.set("site_info", info, 3600)
        return info
