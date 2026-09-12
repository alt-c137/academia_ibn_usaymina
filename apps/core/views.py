"""
Главная страница (лендинг) и страница контактов.

Лендинг собирает данные из других модулей. Чтобы модульность не ломалась,
каждое обращение защищено проверкой apps.is_installed(...) — если модуль
отключён, блок на главной просто не показывается.
"""
from django.apps import apps
from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Главная страница: идея программы → трек курсов → текущий курс →
    метод обучения → оценивание → вопросы → призыв записаться."""

    template_name = "landing/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if apps.is_installed("apps.courses"):
            from apps.courses.models import Course, Program

            context["programs"] = (
                Program.objects.filter(is_published=True)
                .prefetch_related("courses")
                .order_by("order", "pk")
            )
            context["current_course"] = (
                Course.objects.filter(is_published=True, status=Course.Status.ACTIVE)
                .prefetch_related("lessons")
                .first()
            )
            context["register_course"] = (
                Course.objects.filter(is_published=True, status=Course.Status.REGISTRATION)
                .first()
            )
            context["courses_count"] = Course.objects.filter(is_published=True).count()

        if apps.is_installed("apps.news"):
            from apps.news.models import FAQ, Post

            context["latest_posts"] = Post.objects.filter(is_published=True)[:3]
            context["faqs"] = FAQ.objects.filter(is_published=True).order_by("order")[:6]

        return context


def contact_view(request):
    """Страница контактов (WhatsApp, Telegram, почта)."""
    return render(request, "landing/contact.html")


def robots_view(request):
    """robots.txt для поисковиков: закрытые разделы исключаем из индекса."""
    from django.conf import settings

    return render(
        request,
        "robots.txt",
        {"site_url": settings.SITE_URL.rstrip("/")},
        content_type="text/plain",
    )
