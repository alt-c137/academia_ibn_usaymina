"""
Реклама платформы: места (слоты) и материалы (креативы).

Схема для учителя/админа: создаёшь слот («Между записями на главной»),
в него кладёшь креатив — картинку, видео или аудио + ссылку и, если надо,
окно показа (даты). Код сайта не трогается никогда.
"""
from django.db import models

from apps.core.models import TimeStampedModel


class AdSlot(models.Model):
    """Место на сайте, где может показываться реклама."""

    class Location(models.TextChoices):
        HEADER = "header", "Под шапкой"
        SIDEBAR = "sidebar", "Сбоку"
        BETWEEN_POSTS = "between_posts", "Между записями (лента главной)"
        FOOTER = "footer", "Над подвалом"

    name = models.CharField("Название слота", max_length=100,
                            help_text="Для себя: «Главная — между записями»")
    location = models.CharField("Расположение", max_length=20,
                                choices=Location.choices, unique=True)
    is_active = models.BooleanField("Слот активен", default=True)

    class Meta:
        verbose_name = "Рекламный слот"
        verbose_name_plural = "Рекламные слоты"

    def __str__(self):
        return f"{self.get_location_display()} — {self.name}"

    def active_creative(self):
        """Актуальный креатив: активен и внутри окна показа (если задано)."""
        from django.utils import timezone

        today = timezone.localdate()
        return (
            self.creatives.filter(is_active=True)
            .filter(models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=today))
            .filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=today))
            .first()
        )


class AdCreative(TimeStampedModel):
    """Конкретный рекламный материал."""

    slot = models.ForeignKey(
        AdSlot, on_delete=models.CASCADE, related_name="creatives",
        verbose_name="Слот",
    )
    advertiser_name = models.CharField("Кто разместил", max_length=150, blank=True)
    image = models.ImageField("Картинка", upload_to="ads/images/", blank=True)
    video = models.FileField("Видео", upload_to="ads/video/", blank=True)
    audio = models.FileField("Аудио", upload_to="ads/audio/", blank=True)
    link_url = models.URLField("Куда ведёт", blank=True)
    starts_at = models.DateField("Показывать с", null=True, blank=True)
    ends_at = models.DateField("Показывать до", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Рекламный материал"
        verbose_name_plural = "Рекламные материалы"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.advertiser_name or 'Креатив'} → {self.slot}"
