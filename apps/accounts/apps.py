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
    """Создаёт служебные группы и выдаёт права. Запускается после migrate.

    Группы и их возможности (назначаются в админке → Пользователи → Группы):
      «Учитель»             — весь учебный контент: курсы/уроки, экзамены,
                              задания, оценки, библиотека, новости, книги;
                              плюс учительская /teacher/ (проверка работ).
      «Модератор форума»    — темы и ответы форума: одобрение, правка,
                              закрепление, удаление; очередь /forum/moderation/.
      «Редактор новостей»   — новости и FAQ: публикация и правка.
    Суперпользователь и так всё может; is_staff даёт админку.
    """
    from django.contrib.auth.models import Group, Permission

    group, _ = Group.objects.get_or_create(name="Учитель")
    CONTENT_APPS = ("courses", "exams", "assignments", "grading", "library",
                    "news", "books", "payments", "forum", "hadith")
    perms = Permission.objects.filter(content_type__app_label__in=CONTENT_APPS).exclude(
        content_type__app_label="auth"
    )
    # просмотровая доступ к списку студентов (нужен для поиска в заданиях)
    perms = perms | Permission.objects.filter(
        content_type__app_label="accounts", codename__startswith="view"
    )
    group.permissions.set(perms)

    # «Модератор форума» — только темы/ответы форума
    forum_group, _ = Group.objects.get_or_create(name="Модератор форума")
    forum_group.permissions.set(
        Permission.objects.filter(content_type__app_label="forum")
    )

    # «Редактор новостей» — новости и FAQ
    news_group, _ = Group.objects.get_or_create(name="Редактор новостей")
    news_group.permissions.set(
        Permission.objects.filter(content_type__app_label="news")
    )
