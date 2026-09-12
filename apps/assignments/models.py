"""
Еженедельные задания (как на hdat.sa: «еженедельные задания, доступные
до конца курса», 25% итоговой оценки).

  Assignment — задание у курса (текст + опциональный файл для ответа)
  Submission — ответ студента; повторная отправка обновляет прежнюю
               (до дедлайна можно улучшать ответ), учитель ставит баллы
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.validators import ASSIGNMENT_TYPES, FileValidator

SUBMISSION_FILE_MAX_MB = 100


class Assignment(TimeStampedModel):
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="assignments",
        verbose_name="Курс",
    )
    week = models.PositiveSmallIntegerField("Неделя", default=1)
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Текст задания")
    max_points = models.PositiveSmallIntegerField("Максимум баллов", default=5)
    due_at = models.DateTimeField("Сдать до", null=True, blank=True)
    allow_file = models.BooleanField("Разрешить файл в ответе", default=True,
                                     help_text="Фото, аудио, PDF и другие документы")
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ("course", "week", "pk")

    def __str__(self):
        return f"{self.course} — неделя {self.week}: {self.title}"


class Submission(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Отправлено"
        GRADED = "graded", "Проверено"

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions",
        verbose_name="Задание",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions",
        verbose_name="Студент",
    )
    text = models.TextField("Текст ответа", blank=True)
    file = models.FileField(
        "Файл ответа (фото / аудио / PDF)", upload_to="assignments/%Y/", blank=True,
        validators=[FileValidator(ASSIGNMENT_TYPES, max_size_mb=SUBMISSION_FILE_MAX_MB)],
    )

    status = models.CharField("Статус", max_length=10, choices=Status.choices,
                              default=Status.SUBMITTED)
    score = models.DecimalField("Баллы", max_digits=5, decimal_places=1, null=True, blank=True)
    feedback = models.TextField("Комментарий учителя", blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="graded_submissions", verbose_name="Проверил",
    )
    graded_at = models.DateTimeField("Проверено", null=True, blank=True)

    class Meta:
        verbose_name = "Ответ на задание"
        verbose_name_plural = "Ответы на задания"
        constraints = [
            models.UniqueConstraint(fields=("assignment", "student"), name="uniq_submission"),
        ]
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.student} — {self.assignment}"

    @property
    def is_image(self) -> bool:
        """Файл ответа — картинка (показываем превью)."""
        if not self.file:
            return False
        return self.file.name.rsplit(".", 1)[-1].lower() in {"jpg", "jpeg", "png", "gif", "webp"}

    @property
    def is_audio(self) -> bool:
        """Файл ответа — аудио (показываем плеер)."""
        if not self.file:
            return False
        return self.file.name.rsplit(".", 1)[-1].lower() in {"mp3", "m4a", "aac", "ogg", "wav"}
