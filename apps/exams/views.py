"""
Прохождение теста:

  /exams/<id>/            — правила, статистика попыток, кнопка «Начать»
  POST /exams/<id>/start/ — создать попытку и перейти к вопросам
  /exams/attempt/<id>/    — страница вопросов (таймер запускается в шаблоне)
  POST submit             — отправка ответов → автопроверка → результат
  /exams/attempt/<id>/result/ — итог с разбором ошибок
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, TemplateView

from apps.courses.models import Enrollment
from apps.exams.forms import build_exam_form, parse_answers
from apps.exams.models import Attempt, Exam, Question


def _get_enrollment(user, course):
    return Enrollment.objects.filter(student=user, course=course).first()


class ExamDetailView(LoginRequiredMixin, DetailView):
    """Страница-инструкция перед тестом."""
    template_name = "exams/exam_detail.html"
    context_object_name = "exam"
    model = Exam

    def get_queryset(self):
        return Exam.objects.filter(is_published=True).select_related("course")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.object
        context["enrollment"] = _get_enrollment(self.request.user, exam.course)
        context["attempts_used"] = exam.attempts_used(self.request.user)
        context["attempts_left"] = exam.attempts_left(self.request.user)
        context["best"] = exam.best_attempt(self.request.user)
        context["has_open_questions"] = exam.questions.filter(
            q_type=Question.Type.OPEN
        ).exists()
        return context


def exam_start_view(request, pk):
    """Создание попытки (кнопка «Начать тест»)."""
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    exam = get_object_or_404(Exam, pk=pk, is_published=True)

    if not _get_enrollment(request.user, exam.course):
        messages.error(request, "Тест доступен только записавшимся на курс.")
        return redirect("courses:detail", slug=exam.course.slug)

    if exam.attempts_left(request.user) <= 0:
        messages.error(request, "Лимит попыток исчерпан.")
        return redirect("exams:detail", pk=exam.pk)

    if request.method != "POST":
        return redirect("exams:detail", pk=exam.pk)

    # Незакрытая попытка того же теста — продолжаем её, а не создаём новую
    unfinished = Attempt.objects.filter(
        exam=exam, student=request.user, finished_at__isnull=True
    ).first()
    attempt = unfinished or Attempt.start_new(request.user, exam)
    return redirect("exams:take", pk=attempt.pk)


class ExamTakeView(LoginRequiredMixin, TemplateView):
    """Страница вопросов теста с таймером."""
    template_name = "exams/exam_take.html"

    def dispatch(self, request, *args, **kwargs):
        self.attempt = get_object_or_404(
            Attempt, pk=kwargs["pk"], student=request.user
        )
        if self.attempt.is_finished:
            return redirect("exams:result", pk=self.attempt.pk)
        # Время вышло (студент вернулся на страницу позже дедлайна) —
        # автоматически закрываем попытку тем, что успело сохраниться.
        if self.attempt.is_expired():
            self.attempt.finish({})
            messages.warning(request, "Время вышло — попытка закрыта автоматически.")
            return redirect("exams:result", pk=self.attempt.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = build_exam_form(self.attempt.exam)
        context["attempt"] = self.attempt
        context["exam"] = self.attempt.exam
        context["form"] = form
        context["seconds_left"] = self.attempt.seconds_left
        return context

    def post(self, request, pk):
        form = build_exam_form(
            self.attempt.exam, data=request.POST, files=request.FILES
        )
        if form.is_valid():
            answers = parse_answers(form, self.attempt.exam)
        else:
            # Ничего не выбрано — тоже валидная ситуация (0 баллов)
            answers = {}
        self.attempt.finish(answers)
        return redirect("exams:result", pk=self.attempt.pk)


class ExamResultView(LoginRequiredMixin, TemplateView):
    """Результат попытки с разбором по вопросам."""
    template_name = "exams/exam_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = get_object_or_404(
            Attempt.objects.select_related("exam", "exam__course"),
            pk=kwargs["pk"],
            student=self.request.user,
        )
        context["attempt"] = attempt
        context["answers"] = attempt.answers.select_related("question").order_by(
            "question__order"
        )
        context["next_url"] = reverse("grading:office")
        return context
