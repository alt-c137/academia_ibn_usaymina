"""
Страницы учительской:

  /teacher/                       — дашборд: что ждёт проверки
  /teacher/submissions/           — ответы на задания
  /teacher/submissions/<id>/      — проверка ответа: баллы + комментарий
  /teacher/attempts/              — попытки экзаменов с открыми вопросами
  /teacher/attempts/<id>/         — ручная оценка открытых ответов
"""
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from apps.assignments.models import Submission
from apps.exams.models import Answer, Attempt
from apps.teacher.forms import GradeAnswerForm, GradeSubmissionForm
from apps.teacher.permissions import TeacherRequiredMixin


def notify(user, title: str, url: str = "") -> None:
    """Уведомление студенту (тихо игнорируем сбои — не критичный путь)."""
    try:
        from apps.accounts.models import Notification

        Notification.objects.create(user=user, title=title, url=url)
    except Exception:
        pass


class DashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "teacher/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_submissions"] = Submission.objects.filter(
            status=Submission.Status.SUBMITTED
        ).select_related("assignment", "assignment__course", "student").order_by("updated_at")[:10]
        context["pending_submissions_count"] = Submission.objects.filter(
            status=Submission.Status.SUBMITTED
        ).count()
        context["pending_attempts"] = (
            Attempt.objects.filter(finished_at__isnull=False)
            .annotate(pending=Count("answers", filter=Q(answers__needs_grading=True)))
            .filter(pending__gt=0)
            .select_related("exam", "exam__course", "student")
            .order_by("finished_at")[:10]
        )
        context["pending_attempts_count"] = (
            Attempt.objects.filter(finished_at__isnull=False)
            .annotate(pending=Count("answers", filter=Q(answers__needs_grading=True)))
            .filter(pending__gt=0)
            .count()
        )
        return context


class SubmissionListView(TeacherRequiredMixin, ListView):
    template_name = "teacher/submissions.html"
    context_object_name = "submissions"
    paginate_by = 30

    def get_queryset(self):
        queryset = (
            Submission.objects.select_related("assignment", "assignment__course", "student")
            .order_by("-updated_at")
        )
        status = self.request.GET.get("status", "submitted")
        if status in ("submitted", "graded"):
            queryset = queryset.filter(status=status)
        self.extra_context = {"current_status": status}
        return queryset


class SubmissionDetailView(TeacherRequiredMixin, DetailView):
    template_name = "teacher/submission_detail.html"
    context_object_name = "submission"
    model = Submission

    def get_queryset(self):
        return Submission.objects.select_related(
            "assignment", "assignment__course", "student"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = GradeSubmissionForm(instance=self.object)
        return context

    def post(self, request, pk):
        submission = self.object = self.get_queryset().get(pk=pk)
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            if submission.score is not None:
                # Баллы выставлены — ответ считается проверенным
                submission.status = Submission.Status.GRADED
                submission.graded_by = request.user
                submission.graded_at = timezone.now()
            submission.save()
            notify(
                submission.student,
                f"Задание проверено: «{submission.assignment.title}»"
                + (f" — {submission.score}/{submission.assignment.max_points} баллов"
                   if submission.score is not None else
                   " — учитель оставил комментарий"),
                f"/assignments/{submission.assignment_id}/",
            )
            messages.success(
                request,
                "Оценка сохранена." if submission.score is not None else "Комментарий сохранён.",
            )
            return redirect("teacher:submissions")
        messages.error(request, "Проверьте баллы.")
        context = self.get_context_data(object=submission)
        context["form"] = form
        return self.render_to_response(context)


class AttemptListView(TeacherRequiredMixin, ListView):
    """Попытки, где есть открытые ответы без оценки."""
    template_name = "teacher/attempts.html"
    context_object_name = "attempts"
    paginate_by = 30

    def get_queryset(self):
        return (
            Attempt.objects.filter(finished_at__isnull=False)
            .annotate(pending=Count("answers", filter=Q(answers__needs_grading=True)))
            .filter(pending__gt=0)
            .select_related("exam", "exam__course", "student")
            .order_by("finished_at")
        )


class AttemptDetailView(TeacherRequiredMixin, DetailView):
    template_name = "teacher/attempt_detail.html"
    context_object_name = "attempt"
    model = Attempt

    def get_queryset(self):
        return Attempt.objects.select_related("exam", "exam__course", "student")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_answers"] = (
            self.object.answers.filter(needs_grading=True)
            .select_related("question")
            .order_by("question__order")
        )
        context["auto_answers"] = (
            self.object.answers.filter(needs_grading=False)
            .select_related("question")
            .order_by("question__order")
        )
        return context

    def post(self, request, pk):
        """Оценка одного открытого ответа (форма под каждым ответом)."""
        attempt = self.object = self.get_queryset().get(pk=pk)
        answer = get_object_or_404(
            Answer, pk=request.POST.get("answer"), attempt=attempt, needs_grading=True
        )
        form = GradeAnswerForm(request.POST)
        if form.is_valid():
            attempt.grade_open_answer(
                answer,
                points=form.cleaned_data["points"],
                feedback=form.cleaned_data["feedback"],
            )
            notify(
                attempt.student,
                f"Экзамен проверен: «{attempt.exam.title}» — {attempt.score_percent}%",
                f"/exams/result/{attempt.pk}/",
            )
            messages.success(request, "Ответ оценён.")
            # Все открытые ответы проверены — итог попытки пересчитан
            if not attempt.is_pending_manual:
                messages.info(
                    request,
                    f"Проверка завершена: {attempt.student} — "
                    f"{attempt.score_percent}% ({'зачёт' if attempt.passed else 'не зачтено'}).",
                )
            return redirect("teacher:attempt", pk=attempt.pk)
        messages.error(request, "Проверьте баллы.")
        context = self.get_context_data(object=attempt)
        context["error_answer"] = answer
        return self.render_to_response(context)
