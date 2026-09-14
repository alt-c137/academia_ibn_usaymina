"""
Главная страница (лендинг) и страница контактов.

Лендинг собирает данные из других модулей. Чтобы модульность не ломалась,
каждое обращение защищено проверкой apps.is_installed(...) — если модуль
отключён, блок на главной просто не показывается.
"""
from django.apps import apps
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Главная: hero → хаб разделов → кабинет → хадис дня → текущий курс →
    метод → оценивание → лента новостей/форума/уроков → книги → вопросы → CTA."""

    template_name = "landing/home.html"
    feed_page_size = 9

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feed"] = self._build_feed()

        # --- Блок «Ваш кабинет» (только для вошедших) -------------------------
        user = self.request.user
        if user.is_authenticated:
            from apps.courses.models import Enrollment

            context["cabinet_active_courses"] = user.enrollments.exclude(
                status__in=["dropped", "listener"]
            ).count()

        # --- Хадис дня (модуль hadith) ----------------------------------------
        if apps.is_installed("apps.hadith"):
            from apps.core.models import SiteInfo
            from apps.hadith.services import get_hadith_of_the_day

            site = SiteInfo.load()
            if site is None or site.hadith_enabled:
                context["hadith_of_the_day"] = get_hadith_of_the_day()

        # --- Курсы, факультеты (как раньше) ------------------------------------
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
            from apps.news.models import FAQ

            context["faqs"] = FAQ.objects.filter(is_published=True).order_by("order")[:6]

        # Витрина книг на главной (если модуль включён и не выключен в админке)
        if apps.is_installed("apps.books"):
            from apps.books.models import Book
            from apps.core.models import SiteInfo

            site = SiteInfo.load()
            if site is None or site.show_books:
                context["home_books"] = Book.objects.filter(is_published=True)[:4]

        return context

    def _build_feed(self):
        """Единая лента: новости + темы форума + свежие уроки открытых курсов.

        Каждая запись: kind / title / url / date / meta. Сортировка по дате,
        пагинация по feed_page_size записей (аргумент ?page=).
        """
        items = []

        if apps.is_installed("apps.news"):
            from apps.news.models import Post as NewsPost

            for post in NewsPost.objects.filter(is_published=True)[:12]:
                items.append({
                    "kind": "news",
                    "title": post.title,
                    "url": post.get_absolute_url(),
                    "date": post.published_at or post.created_at,
                    "cover": post.cover,
                    "excerpt": post.excerpt,
                })

        if apps.is_installed("apps.forum"):
            from apps.core.sections import section_enabled
            from apps.forum.models import Thread

            if section_enabled("forum_enabled"):
                for thread in (
                    Thread.objects.filter(is_approved=True)
                    .select_related("author", "board")
                    .order_by("-updated_at")[:12]
                ):
                    items.append({
                        "kind": "forum",
                        "title": thread.title,
                        "url": thread.get_absolute_url(),
                        "date": thread.last_activity or thread.created_at,
                        "author": str(thread.author or ""),
                        "replies": thread.posts.count(),
                        "board": thread.board.name,
                    })

        if apps.is_installed("apps.courses"):
            from apps.courses.models import Lesson

            for lesson in (
                Lesson.objects.filter(
                    is_published=True,
                    course__is_published=True,
                    course__status__in=["registration", "active"],
                )
                .select_related("course")
                .order_by("-created_at")[:12]
            ):
                items.append({
                    "kind": "lesson",
                    "title": lesson.title,
                    "url": None,  # урок открыт только записанным — ведём на курс
                    "alt_url": lesson.course.get_absolute_url(),
                    "date": lesson.created_at,
                    "course": lesson.course.title,
                    "week": lesson.week,
                })

        items.sort(key=lambda i: i["date"], reverse=True)
        paginator = Paginator(items, self.feed_page_size)
        page_number = self.request.GET.get("page") or 1
        return paginator.get_page(page_number)


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
