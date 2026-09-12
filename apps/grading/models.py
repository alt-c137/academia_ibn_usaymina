"""
Посещаемость встреч (5% итога) и академическая выписка.

Выписка — «снимок» оценок студента на момент формирования: даже если курс потом
изменится, выданная выписка остаётся верной. Код выписки используется для
подтверждения подлинности (проверяющий находит по коду в админке).
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Attendance(models.Model):
    """Отметка о присутствии студента на научной встрече. Ставит учитель."""

    enrollment = models.ForeignKey(
        "courses.Enrollment", on_delete=models.CASCADE, related_name="attendance",
        verbose_name="Запись на курс",
    )
    date = models.DateField("Дата встречи")
    present = models.BooleanField("Присутствовал", default=True)
    note = models.CharField("Заметка", max_length=200, blank=True)

    class Meta:
        verbose_name = "Посещение встречи"
        verbose_name_plural = "Посещение встреч"
        ordering = ("enrollment", "date")
        constraints = [
            models.UniqueConstraint(fields=("enrollment", "date"), name="uniq_attendance_per_day"),
        ]

    def __str__(self):
        return f"{self.enrollment} — {self.date:%d.%m.%Y}"


class Transcript(TimeStampedModel):
    """Академическая выписка (выдаётся вместо сертификата, как на hdat.sa)."""

    enrollment = models.OneToOneField(
        "courses.Enrollment", on_delete=models.CASCADE, related_name="transcript",
        verbose_name="Запись на курс",
    )
    # Снимок данных на момент выдачи
    student_name = models.CharField("Студент", max_length=220)
    course_title = models.CharField("Курс", max_length=220)
    exam_points = models.DecimalField("Экзамен (макс. 70)", max_digits=5, decimal_places=1)
    assignment_points = models.DecimalField("Задания (макс. 25)", max_digits=5, decimal_places=1)
    activity_points = models.DecimalField("Активность (макс. 5)", max_digits=5, decimal_places=1)
    total_points = models.DecimalField("Итого (макс. 100)", max_digits=5, decimal_places=1)
    passed = models.BooleanField("Зачёт (порог 60)", default=False)

    code = models.CharField("Код выписки", max_length=8, unique=True, editable=False)

    class Meta:
        verbose_name = "Академическая выписка"
        verbose_name_plural = "Академические выписки"

    def __str__(self):
        return f"Выписка {self.code} — {self.student_name} — {self.course_title}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)
