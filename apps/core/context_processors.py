"""
Контекст-процессор: подмешивает к каждому шаблону название сайта, контакты
и список установленных модулей (чтобы шаблоны могли показывать/прятать блоки).
"""
from django.apps import apps as django_apps
from django.conf import settings
from django.core.cache import cache


def site_info(request):
    from apps.core.models import SiteInfo

    site = SiteInfo.load()
    context = {
        "site": site,
        # Алиас по ТЗ: один и тот же объект настроек сайта
        "site_settings": site,
        # Название в шапке: сначала из админки (меняется на лету),
        # затем из .env (SITE_NAME), затем запасной вариант.
        "site_title": (site.site_name if site else "") or settings.SITE_NAME,
        "has_exams": django_apps.is_installed("apps.exams"),
        "has_assignments": django_apps.is_installed("apps.assignments"),
        "has_grading": django_apps.is_installed("apps.grading"),
        # Библиотека/форум: модуль установлен И включён в настройках сайта
        "has_library": (
            django_apps.is_installed("apps.library")
            and (site is None or site.library_enabled)
        ),
        "has_news": django_apps.is_installed("apps.news"),
        "has_meetings": django_apps.is_installed("apps.meetings"),
        "has_hadith": (
            django_apps.is_installed("apps.hadith")
            and (site is None or site.hadith_enabled)
        ),
        # Форум: показываем в меню и при выключенном комментарии
        "has_forum": (
            django_apps.is_installed("apps.forum")
            and (site is None or site.forum_enabled)
        ),
        "has_payments": django_apps.is_installed("apps.payments"),
        # Книги: модуль включён И переключатель в админке включён
        # (нет записи в админке — считаем включённым)
        "has_books": (
            django_apps.is_installed("apps.books")
            and (site is None or site.show_books)
        ),
    }

    # Ссылка «Учительская» + счётчик непроверенного (кэш на минуту,
    # чтобы не считать на каждом запросе)
    context["user_is_teacher"] = False
    context["teacher_pending"] = 0
    context["unread_notifications"] = 0
    if request.user.is_authenticated:
        # Непрочитанные уведомления — для колокола в шапке
        if django_apps.is_installed("apps.accounts"):
            from apps.accounts.models import Notification

            context["unread_notifications"] = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()

        try:
            from apps.teacher.permissions import is_teacher

            context["user_is_teacher"] = is_teacher(request.user)
        except Exception:
            context["user_is_teacher"] = request.user.is_staff
        if context["user_is_teacher"]:
            pending = cache.get("teacher_pending_count")
            if pending is None:
                pending = _count_pending()
                cache.set("teacher_pending_count", pending, 60)
            context["teacher_pending"] = pending

            # Очередь модерации форума (модуль forum)
            if django_apps.is_installed("apps.forum"):
                from apps.forum.models import Thread

                forum_pending = cache.get("forum_pending_count")
                if forum_pending is None:
                    forum_pending = Thread.objects.filter(is_approved=False).count()
                    cache.set("forum_pending_count", forum_pending, 60)
                context["forum_pending"] = forum_pending

    return context


def _count_pending() -> int:
    """Сколько ответов ждут проверки учителя (задания + экзамены)."""
    total = 0
    from django.apps import apps

    if apps.is_installed("apps.assignments"):
        from apps.assignments.models import Submission

        total += Submission.objects.filter(status=Submission.Status.SUBMITTED).count()
    if apps.is_installed("apps.exams"):
        from apps.exams.models import Answer

        total += Answer.objects.filter(needs_grading=True).count()
    return total
