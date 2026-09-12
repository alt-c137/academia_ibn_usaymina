"""
Экзамены с проверкой знаний двух видов:

  автопроверка   — вопросы «один ответ» / «несколько ответов» (мгновенно)
  ручная проверка — вопросы «свободный ответ»: студент пишет текст и/или
                    крепит файл (фото, аудио), учитель выставляет баллы
                    с комментарием в учительской (/teacher/)

  Exam     — тест у курса (итоговый экзамен или промежуточный тест)
  Question — вопрос
  Choice   — вариант ответа (для вопросов с выбором)
  Attempt  — попытка прохождения (таймер, баллы, зачёт)
  Answer   — ответ на конкретный вопрос внутри попытки

Логика автопроверки вопроса с выбором:
  один ответ  — выбран ровно правильный вариант;
  несколько   — выбраны все правильные и ни одного лишнего (строгое совпадение).
Незакрытые вопросы приносят 0 баллов и не блокируют отправку.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.validators import ASSIGNMENT_TYPES, FileValidator


class Exam(TimeStampedModel):
    class Kind(models.TextChoices):
        FINAL = "final", "Итоговый экзамен"
        MODULE = "module", "Промежуточный тест"

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="exams", verbose_name="Курс"
    )
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание / инструкция", blank=True)
    kind = models.CharField("Тип", max_length=10, choices=Kind.choices, default=Kind.FINAL)
    time_limit_min = models.PositiveSmallIntegerField("Лимит времени, минут", default=45)
    max_attempts = models.PositiveSmallIntegerField("Максимум попыток", default=3)
    pass_percent = models.PositiveSmallIntegerField("Порог зачёта, %", default=60)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Тест / экзамен"
        verbose_name_plural = "Тесты и экзамены"
        ordering = ("course", "kind", "pk")

    def __str__(self):
        return f"{self.title} ({self.course})"

    def attempts_used(self, student) -> int:
        return self.attempts.filter(student=student).count()

    def attempts_left(self, student) -> int:
        return max(0, self.max_attempts - self.attempts_used(student))

    def best_attempt(self, student):
        """Лучшая ПОЛНОСТЬЮ проверенная попытка (без ждущих ручной оценки)."""
        attempts = (
            self.attempts.filter(student=student, finished_at__isnull=False)
            .order_by("-score_percent", "-finished_at")
            .select_related("exam")
        )
        for attempt in attempts:
            if not attempt.is_pending_manual:
                return attempt
        return None


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = "single", "Один ответ"
        MULTI = "multi", "Несколько ответов"
        OPEN = "open", "Свободный ответ (проверяет учитель)"

    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="questions", verbose_name="Тест"
    )
    order = models.PositiveSmallIntegerField("Порядок", default=1)
    text = models.TextField("Текст вопроса")
    q_type = models.CharField("Тип вопроса", max_length=10, choices=Type.choices,
                              default=Type.SINGLE)
    points = models.PositiveSmallIntegerField("Баллы", default=1)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ("exam", "order")

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices", verbose_name="Вопрос"
    )
    order = models.PositiveSmallIntegerField("Порядок", default=1)
    text = models.CharField("Текст варианта", max_length=400)
    is_correct = models.BooleanField("Правильный", default=False)

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        ordering = ("question", "order")

    def __str__(self):
        mark = "✓ " if self.is_correct else ""
        return f"{mark}{self.text}"


class Attempt(TimeStampedModel):
    """Одна попытка прохождения теста. Создаётся при старте, закрывается
    методом finish() — он же считает баллы (автопроверка)."""

    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="attempts", verbose_name="Тест"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts",
        verbose_name="Студент",
    )
    started_at = models.DateTimeField("Начато", auto_now_add=True)
    finished_at = models.DateTimeField("Завершено", null=True, blank=True)
    points_earned = models.PositiveSmallIntegerField("Набрано баллов", default=0)
    points_max = models.PositiveSmallIntegerField("Максимум баллов", default=0)
    score_percent = models.PositiveSmallIntegerField("Результат, %", default=0)
    passed = models.BooleanField("Зачёт", default=False)

    class Meta:
        verbose_name = "Попытка прохождения"
        verbose_name_plural = "Попытки прохождения"
        ordering = ("-started_at",)

    def __str__(self):
        return f"{self.student} — {self.exam} — {self.score_percent}%"

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    @property
    def deadline(self):
        """Момент, после которого ответы не принимаются."""
        from datetime import timedelta

        return self.started_at + timedelta(minutes=self.exam.time_limit_min)

    @property
    def seconds_left(self) -> int:
        """Сколько секунд осталось до дедлайна (0, если вышел)."""
        delta = self.deadline - timezone.now()
        return max(0, int(delta.total_seconds()))

    # --- Оспаривание лимита времени -------------------------------------
    GRACE_SECONDS = 60  # запас на медленный интернет при отправке ответов

    def is_expired(self) -> bool:
        return (timezone.now() - self.deadline).total_seconds() > self.GRACE_SECONDS

    # --- Основная логика --------------------------------------------------
    @classmethod
    def start_new(cls, student, exam) -> "Attempt":
        """Создаёт попытку; исключение, если лимит попыток исчерпан."""
        if exam.attempts_left(student) <= 0:
            raise PermissionError("Лимит попыток исчерпан")
        points_max = sum(
            q["points"] for q in exam.questions.values("points")
        )
        return cls.objects.create(student=student, exam=exam, points_max=points_max)

    def finish(self, answers: dict) -> None:
        """Закрытие попытки и автопроверка.

        answers: {id вопроса: {"choices": [id вариантов], "text": str, "file": файл}}
        Вопросы с выбором проверяются сразу; открытые вопросы уходят учителю
        (needs_grading). Повторный вызов игнорируется.
        """
        if self.is_finished:
            return

        questions = list(
            self.exam.questions.prefetch_related("choices").order_by("order")
        )
        correct_map = {
            q.id: set(q.choices.filter(is_correct=True).values_list("id", flat=True))
            for q in questions
        }

        earned = 0
        Answer.objects.filter(attempt=self).delete()
        for question in questions:
            entry = answers.get(question.id) or {}
            if isinstance(entry, (list, tuple)):  # старый формат: список вариантов
                entry = {"choices": entry}
            if question.q_type == question.Type.OPEN:
                Answer.objects.create(
                    attempt=self,
                    question=question,
                    text=entry.get("text", ""),
                    file=entry.get("file") or None,
                    needs_grading=True,
                )
                continue  # баллы открытому вопросу выставит учитель

            selected = set(map(int, entry.get("choices", [])))
            is_ok = bool(correct_map[question.id]) and selected == correct_map[question.id]
            points = question.points if is_ok else 0
            Answer.objects.create(
                attempt=self, question=question, is_correct=is_ok, points=points
            )
            earned += points

        self.points_max = sum(q.points for q in questions)
        self.points_earned = earned
        self.score_percent = round(earned / self.points_max * 100) if self.points_max else 0
        self.passed = self.score_percent >= self.exam.pass_percent
        self.finished_at = timezone.now()
        self.save()

    @property
    def is_pending_manual(self) -> bool:
        """Есть ответы, ожидающие ручной оценки учителя."""
        return self.answers.filter(needs_grading=True).exists()

    @property
    def status_label(self) -> str:
        if not self.is_finished:
            return "В процессе"
        return "На проверке учителя" if self.is_pending_manual else "Проверено"

    def grade_open_answer(self, answer: "Answer", points: int, feedback: str = "") -> None:
        """Учитель оценил открытый ответ — фиксируем и пересчитываем итог."""
        answer.points = min(max(int(points), 0), answer.question.points)
        answer.feedback = feedback
        answer.needs_grading = False
        answer.save(update_fields=["points", "feedback", "needs_grading"])
        self.refresh_score()

    def refresh_score(self) -> None:
        """Пересчёт итога по всем ответам попытки (после ручных оценок)."""
        earned = sum(self.answers.values_list("points", flat=True)) or 0
        self.points_earned = earned
        self.score_percent = round(earned / self.points_max * 100) if self.points_max else 0
        self.passed = self.score_percent >= self.exam.pass_percent
        self.save(update_fields=["points_earned", "score_percent", "passed"])


class Answer(models.Model):
    attempt = models.ForeignKey(
        Attempt, on_delete=models.CASCADE, related_name="answers", verbose_name="Попытка"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers", verbose_name="Вопрос"
    )
    is_correct = models.BooleanField("Верно", default=False)
    points = models.PositiveSmallIntegerField("Баллы", default=0)
    # --- поля открытого ответа (проверяет учитель) ---
    text = models.TextField("Текст ответа", blank=True)
    file = models.FileField(
        "Файл ответа (фото/аудио/PDF)", upload_to="exam-answers/%Y/", blank=True,
        validators=[FileValidator(ASSIGNMENT_TYPES, max_size_mb=100)],
    )
    needs_grading = models.BooleanField("Ждёт оценки учителя", default=False)
    feedback = models.TextField("Комментарий учителя", blank=True)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ("attempt", "question__order")
