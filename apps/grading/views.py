"""
Кабинет студента (/office/) и академическая выписка (/office/transcript/).

Кабинет — сборная страница: прогресс по курсам, задания к сдаче, результаты
тестов, итоговые баллы. Блоки модулей, которые отключены, не показываются.
"""
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.courses.models import Enrollment
from apps.grading.services import compute_course_grade, issue_transcript


class OfficeView(LoginRequiredMixin, TemplateView):
    """Кабинет студента."""
    template_name = "grading/office.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        enrollments = list(
            Enrollment.objects.filter(student=user)
            .exclude(status=Enrollment.Status.DROPPED)
            .select_related("course", "course__program")
            .prefetch_related("course__lessons")
        )
        context["enrollments"] = enrollments
        context["grades"] = {e.pk: compute_course_grade(e) for e in enrollments}

        # Группировка по факультетам (программам): «Факультет акыды — 42%».
        # Прогресс программы = средний прогресс её курсов у студента.
        by_program: dict[int, dict] = {}
        for e in enrollments:
            program = e.course.program
            row = by_program.setdefault(program.pk, {"program": program, "items": []})
            row["items"].append(e)
        program_rows = []
        for row in by_program.values():
            row["percent"] = round(
                sum(e.percent for e in row["items"]) / len(row["items"])
            )
            program_rows.append(row)
        program_rows.sort(key=lambda r: (r["program"].order, r["program"].pk))
        context["program_rows"] = program_rows

        if apps.is_installed("apps.assignments"):
            from apps.assignments.models import Assignment, Submission

            course_ids = [e.course_id for e in enrollments]
            pending = []
            for assignment in (
                Assignment.objects.filter(course_id__in=course_ids, is_published=True)
                .filter(due_at__isnull=False, due_at__gte=timezone.now())
                .select_related("course")
                .order_by("due_at")
            ):
                submission = assignment.submissions.filter(student=user).first()
                if submission is None or submission.status == submission.Status.SUBMITTED:
                    pending.append(assignment)
            context["pending_assignments"] = pending[:6]

        if apps.is_installed("apps.exams"):
            from apps.exams.models import Attempt

            context["recent_attempts"] = (
                Attempt.objects.filter(student=user, finished_at__isnull=False)
                .select_related("exam", "exam__course")
                .order_by("-finished_at")[:5]
            )

        context["has_transcripts"] = user.enrollments.filter(
            transcript__isnull=False
        ).exists()

        # Ближайшая онлайн-встреча (если модуль meetings включён)
        if apps.is_installed("apps.meetings"):
            from apps.meetings.models import Meeting

            context["next_meeting"] = (
                Meeting.objects.filter(is_published=True, starts_at__gte=timezone.now())
                .select_related("course")
                .order_by("starts_at")
                .first()
            )

        # Счётчик неоплаченных частей — бейдж на кнопке «Платежи»
        if apps.is_installed("apps.payments"):
            from apps.payments.models import Installment, Invoice

            context["my_unpaid"] = Installment.objects.filter(
                invoice__student=user, invoice__is_active=True, is_paid=False
            ).count()

        return context


class TranscriptView(LoginRequiredMixin, TemplateView):
    """Выписка по всем курсам студента (печатная — отдельные стили печати)."""
    template_name = "grading/transcript.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Выписка — формальный документ: только зачисленные курсы,
        # свободных слушателей в неё не включаем.
        enrollments = list(
            Enrollment.objects.filter(student=self.request.user)
            .exclude(status__in=[Enrollment.Status.DROPPED, Enrollment.Status.LISTENER])
            .select_related("course", "course__program")
        )
        context["rows"] = [
            {
                "enrollment": e,
                "grade": compute_course_grade(e),
                "transcript": getattr(e, "transcript", None),
            }
            for e in enrollments
        ]
        return context

    def post(self, request):
        """Кнопка «Сформировать выписку» у конкретного курса."""
        enrollment_pk = request.POST.get("enrollment")
        enrollment = get_object_or_404(
            Enrollment, pk=enrollment_pk, student=request.user
        )
        issue_transcript(enrollment)
        return redirect("grading:transcript")
