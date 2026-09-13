"""
Онлайн-лекции (созвоны): учитель преподаёт вживую по ссылке
(Zoom, Google Meet, YouTube-трансляция — любая).

  Meeting — одна встреча: дата-время, длительность, ссылка подключения.
  Статус считается сам: запланирована → идёт сейчас → завершена.

Посещаемость для оценки (5%) отмечает учитель в модуле grading (Посещение встреч).
"""
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Meeting(TimeStampedModel):
    class Status:
        UPCOMING = "upcoming"
        LIVE = "live"
        FINISHED = "finished"

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="meetings",
        verbose_name="Курс", null=True, blank=True,
        help_text="Пусто — общая встреча платформы",
    )
    title = models.CharField("Тема встречи", max_length=250)
    description = models.TextField("Описание / план", blank=True)
    starts_at = models.DateTimeField("Начало")
    duration_min = models.PositiveSmallIntegerField("Длительность, минут", default=60)
    link = models.URLField(
        "Ссылка подключения", blank=True,
        help_text="Zoom / Google Meet / YouTube-трансляция. Видна записавшимся.",
    )
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Онлайн-встреча"
        verbose_name_plural = "Онлайн-встречи"
        ordering = ("starts_at",)

    def __str__(self):
        return f"{self.starts_at:%d.%m.%Y %H:%M} — {self.title}"

    @property
    def ends_at(self):
        return self.starts_at + timedelta(minutes=self.duration_min)

    @property
    def status(self) -> str:
        now = timezone.now()
        if now < self.starts_at:
            return self.Status.UPCOMING
        if now <= self.ends_at:
            return self.Status.LIVE
        return self.Status.FINISHED

    @property
    def status_display(self) -> str:
        return {
            self.Status.UPCOMING: "Запланирована",
            self.Status.LIVE: "Идёт сейчас",
            self.Status.FINISHED: "Завершена",
        }[self.status]

    @property
    def show_link(self) -> bool:
        """Ссылку показываем во время встречи и незадолго до начала (15 минут)."""
        from datetime import timedelta as td

        return self.status != self.Status.FINISHED and (
            timezone.now() >= self.starts_at - td(minutes=15)
        )
