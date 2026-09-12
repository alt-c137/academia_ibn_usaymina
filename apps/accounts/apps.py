from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Пользователи"

    def ready(self):
        # После применения миграций гарантируем наличие группы «Учитель»
        # с правами на контент платформы (см. apps/teacher/permissions.py)
        post_migrate.connect(ensure_teacher_group, sender=self)


def ensure_teacher_group(sender, **kwargs):
    """Создаёт группу «Учитель» и выдаёт ей права на модули контента.

    Учитель может добавлять уроки/тесты/задания и проверять ответы,
    но не управляет пользователями и настройками сайта.
    Запускается автоматически после каждой команды migrate.
    """
    from django.contrib.auth.models import Group, Permission

    CONTENT_APPS = ("courses", "exams", "assignments", "grading", "library", "news")
    group, _ = Group.objects.get_or_create(name="Учитель")

    perms = Permission.objects.filter(content_type__app_label__in=CONTENT_APPS).exclude(
        content_type__app_label="auth"
    )
    # просмотровая доступ к списку студентов (нужен для поиска в заданиях)
    perms = perms | Permission.objects.filter(
        content_type__app_label="accounts", codename__startswith="view"
    )
    group.permissions.set(perms)
