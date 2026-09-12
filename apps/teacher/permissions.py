"""
Доступ в учительскую.

Учителем считается пользователь, который:
  — отмечен is_staff (админ ставит галочку в админке), или
  — состоит в группе «Учитель» (создаётся автоматически, см. apps/accounts/apps.py).

Суперпользователь — учитель автоматически.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

TEACHER_GROUP = "Учитель"


def is_teacher(user) -> bool:
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name=TEACHER_GROUP).exists()
    )


class TeacherRequiredMixin(LoginRequiredMixin):
    """Примесь для страниц учительской: анонима отправляет на вход,
    вошедшего не-учителя — разворачивает с 403."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()  # редирект на страницу входа
        if not is_teacher(request.user):
            raise PermissionDenied("Раздел доступен только учителям.")
        return super().dispatch(request, *args, **kwargs)
