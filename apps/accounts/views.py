"""
Вход, выход и профиль хранят шаблоны Django (apps/accounts/urls.py),
поэтому здесь — только регистрация, профиль и уведомления.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.accounts.forms import ProfileForm, RegisterForm
from apps.accounts.models import Notification, User


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("grading:office")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # сразу входим после регистрации
        # Женщинам по умолчанию — тема «Роза» (свой выбор важнее настроек)
        if self.object.gender == "female":
            response.set_cookie("theme", "rose", max_age=31536000, samesite="Lax")
        messages.success(self.request, "Добро пожаловать! Аккаунт создан.")
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user  # редактируем только себя

    def get_context_data(self, **kwargs):
        """Краткая сводка рядом с настройками: программы, прогресс, дедлайны."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        from django.utils import timezone

        from apps.assignments.models import Assignment
        from apps.courses.models import Enrollment

        enrollments = list(
            user.enrollments.exclude(status__in=[
                "dropped", "listener",
            ]).select_related("course", "course__program")
        )
        context["enrollments"] = enrollments
        if enrollments:
            context["overall_percent"] = round(
                sum(e.percent for e in enrollments) / len(enrollments)
            )
        context["next_due"] = (
            Assignment.objects.filter(
                course_id__in=[e.course_id for e in enrollments],
                is_published=True,
                due_at__gte=timezone.now(),
            )
            .order_by("due_at")
            .first()
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)


class NotificationsView(LoginRequiredMixin, ListView):
    """Список уведомлений студента (проверки работ, ответы учителя)."""

    template_name = "accounts/notifications.html"
    context_object_name = "notifications"
    paginate_by = 30

    def get_queryset(self):
        return self.request.user.notifications.order_by("-created_at")


def notifications_read_view(request):
    """Кнопка «Отметить всё прочитанным»."""
    if request.method == "POST":
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.info(request, "Все уведомления отмечены прочитанными.")
    return redirect("accounts:notifications")
