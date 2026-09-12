"""
Страница задания: текст задания + форма ответа + история своей отправки.
Доступна только записавшимся на курс. Повторная отправка до дедлайна
обновляет прежний ответ.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from apps.assignments.forms import SubmissionForm
from apps.assignments.models import Assignment, Submission
from apps.courses.models import Enrollment


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    template_name = "assignments/assignment_detail.html"
    context_object_name = "assignment"
    model = Assignment

    def get_queryset(self):
        return Assignment.objects.filter(is_published=True).select_related("course")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.object
        context["enrollment"] = get_object_or_404(
            Enrollment, course=assignment.course, student=self.request.user
        )
        submission = assignment.submissions.filter(student=self.request.user).first()
        context["submission"] = submission
        context["form"] = SubmissionForm(
            instance=submission, allow_file=assignment.allow_file
        )
        context["overdue"] = bool(assignment.due_at and timezone.now() > assignment.due_at)
        return context

    def post(self, request, pk):
        assignment = self.object = self.get_queryset().get(pk=pk)
        get_object_or_404(Enrollment, course=assignment.course, student=request.user)

        if assignment.due_at and timezone.now() > assignment.due_at:
            messages.error(request, "Срок сдачи этого задания истёк.")
            return redirect("assignments:detail", pk=assignment.pk)

        submission = assignment.submissions.filter(student=request.user).first()
        form = SubmissionForm(request.POST, request.FILES,
                              instance=submission, allow_file=assignment.allow_file)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.assignment = assignment
            obj.student = request.user
            obj.status = Submission.Status.SUBMITTED  # на перепроверку
            obj.save()
            messages.success(request, "Ответ отправлен. Да примет Аллах ваши труды!")
            return redirect("assignments:detail", pk=assignment.pk)

        messages.error(request, "Проверьте заполнение полей.")
        context = self.get_context_data(object=assignment)
        context["form"] = form
        return self.render_to_response(context)
