"""
Контекст-процессор: подмешивает к каждому шаблону название сайта, контакты
и список установленных модулей (чтобы шаблоны могли показывать/прятать блоки).
"""
from django.apps import apps as django_apps
from django.conf import settings
from django.core.cache import cache


def site_info(request):
    from apps.core.models import SiteInfo

    context = {
        "site": SiteInfo.load(),
        "site_title": settings.SITE_NAME,
        "has_exams": django_apps.is_installed("apps.exams"),
        "has_assignments": django_apps.is_installed("apps.assignments"),
        "has_grading": django_apps.is_installed("apps.grading"),
        "has_library": django_apps.is_installed("apps.library"),
        "has_news": django_apps.is_installed("apps.news"),
    }

    # Ссылка «Учительская» + счётчик непроверенного (кэш на минуту,
    # чтобы не считать на каждом запросе)
    context["user_is_teacher"] = False
    context["teacher_pending"] = 0
    if request.user.is_authenticated:
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
