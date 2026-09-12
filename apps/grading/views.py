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
        return context


class TranscriptView(LoginRequiredMixin, TemplateView):
    """Выписка по всем курсам студента (печатная — отдельные стили печати)."""
    template_name = "grading/transcript.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollments = list(
            Enrollment.objects.filter(student=self.request.user)
            .exclude(status=Enrollment.Status.DROPPED)
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
