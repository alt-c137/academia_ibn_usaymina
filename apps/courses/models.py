"""
Модель обучения платформы:

  Program  — учебная программа (трек из нескольких курсов, например
             «Коралловые холмы — положения о джиннах»)
  Course   — курс внутри программы (обычно = книга, как 11 книг на hdat.sa)
  Lesson   — урок курса: видео + конспект + PDF + аудио
  Enrollment — запись студента на курс
  LessonProgress — отметка «урок пройден»
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Program(TimeStampedModel):
    name = models.CharField("Название программы", max_length=200)
    slug = models.SlugField("Адрес (латиницей)", max_length=220, unique=True)
    summary = models.CharField("Краткое описание", max_length=300, blank=True)
    description = models.TextField("Полное описание", blank=True)
    order = models.PositiveSmallIntegerField("Порядок вывода", default=1)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"
        ordering = ("order", "pk")

    def __str__(self):
        return self.name


class Course(TimeStampedModel):
    """Курс = книга + уроки + экзамен. Статус курса виден на главной странице
    (как трек книг на hdat.sa/Tases)."""

    class Status(models.TextChoices):
        SOON = "soon", "Скоро"
        REGISTRATION = "registration", "Открыта регистрация"
        ACTIVE = "active", "Идёт обучение"
        FINISHED = "finished", "Завершён"

    program = models.ForeignKey(
        Program, on_delete=models.PROTECT, related_name="courses", verbose_name="Программа"
    )
    title = models.CharField("Название курса", max_length=200)
    slug = models.SlugField("Адрес (латиницей)", max_length=220, unique=True)
    book = models.CharField("Книга", max_length=200, blank=True, help_text="Например: «Коралловые холмы», глава 1–5")
    author = models.CharField("Автор книги", max_length=200, blank=True)
    summary = models.TextField("Кратко о курсе", blank=True)
    description = models.TextField("Подробное описание", blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.SOON)
    cover = models.ImageField("Обложка", upload_to="courses/covers/", blank=True)
    is_free = models.BooleanField(
        "Свободный доступ", default=False,
        help_text="Курс открыт без зачисления: любой зарегистрированный может "
                  "проходить уроки и тесты как свободный слушатель (решает админ)",
    )

    registration_start = models.DateField("Начало регистрации", null=True, blank=True)
    registration_end = models.DateField("Конец регистрации", null=True, blank=True)
    start_date = models.DateField("Начало обучения", null=True, blank=True)
    end_date = models.DateField("Конец обучения", null=True, blank=True)

    order = models.PositiveSmallIntegerField("Порядок в программе", default=1)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ("order", "pk")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("courses:detail", kwargs={"slug": self.slug})

    @property
    def registration_open(self) -> bool:
        """Регистрация открыта: статус позволяет + сегодняшняя дата в окне дат."""
        from django.utils import timezone

        if self.status not in (self.Status.REGISTRATION, self.Status.ACTIVE):
            return False
        today = timezone.localdate()
        if self.registration_start and today < self.registration_start:
            return False
        if self.registration_end and today > self.registration_end:
            return False
        return True

    def is_enrolled(self, user) -> bool:
        if not user.is_authenticated:
            return False
        return self.enrollments.filter(student=user).exists()


class Lesson(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс"
    )
    order = models.PositiveSmallIntegerField("Номер урока")
    week = models.PositiveSmallIntegerField("Неделя", default=1)
    title = models.CharField("Название урока", max_length=250)
    summary = models.TextField("Краткое содержание", blank=True)
    content = models.TextField("Конспект урока", blank=True)
    video_url = models.URLField("Ссылка на видео (YouTube/VK)", blank=True)
    audio = models.FileField("Аудиофайл", upload_to="lessons/audio/%Y/", blank=True)
    document = models.FileField("PDF-файл урока", upload_to="lessons/docs/%Y/", blank=True)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ("course", "order")
        constraints = [
            models.UniqueConstraint(fields=("course", "order"), name="uniq_lesson_order_in_course"),
        ]

    def __str__(self):
        return f"{self.course} — урок {self.order}. {self.title}"

    @property
    def video_embed_url(self) -> str:
        """Превращает обычную ссылку YouTube/VK в ссылку для вставки плеера."""
        url = self.video_url or ""
        if "youtube.com/watch" in url and "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return url


class Enrollment(TimeStampedModel):
    """Запись студента на курс. Одна запись на студента и курс."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Учится"
        COMPLETED = "completed", "Завершил"
        DROPPED = "dropped", "Бросил"
        LISTENER = "listener", "Слушатель (свободно)"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments",
        verbose_name="Студент",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments",
                               verbose_name="Курс")
    status = models.CharField("Статус", max_length=20, choices=Status.choices,
                              default=Status.ACTIVE)

    class Meta:
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курсы"
        constraints = [
            models.UniqueConstraint(fields=("student", "course"), name="uniq_student_per_course"),
        ]

    def __str__(self):
        return f"{self.student} — {self.course}"

    @property
    def lessons_done(self) -> int:
        return self.progress.select_related("lesson").filter(
            lesson__is_published=True
        ).count()

    @property
    def lessons_total(self) -> int:
        return self.course.lessons.filter(is_published=True).count()

    @property
    def percent(self) -> int:
        """Прогресс прохождения уроков, % (0–100)."""
        if not self.lessons_total:
            return 0
        return round(self.lessons_done / self.lessons_total * 100)


class LessonProgress(models.Model):
    """Отметка «урок пройден» (ставит сам студент кнопкой на странице урока)."""

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="progress", verbose_name="Запись"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="progress", verbose_name="Урок"
    )
    completed_at = models.DateTimeField("Пройден", auto_now_add=True)

    class Meta:
        verbose_name = "Прогресс урока"
        verbose_name_plural = "Прогресс уроков"
        constraints = [
            models.UniqueConstraint(fields=("enrollment", "lesson"), name="uniq_progress_per_lesson"),
        ]

    def __str__(self):
        return f"{self.enrollment.student}: {self.lesson}"
