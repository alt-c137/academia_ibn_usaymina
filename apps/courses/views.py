"""
Страницы модуля courses:

  /courses/            — каталог курсов (сгруппирован по программам)
  /courses/<slug>/     — страница курса: описание + уроки + кнопка записаться
  /courses/<slug>/<номер урока>/ — урок (видео, конспект, файлы, «пройдено»)
  POST-действия: записаться на курс, отметить урок пройденным
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from apps.courses.models import Course, Enrollment, Lesson, LessonProgress, Program


class CourseListView(ListView):
    """Каталог: программы с их курсами и статусами (как трек книг на hdat.sa)."""
    template_name = "courses/course_list.html"
    context_object_name = "programs"

    def get_queryset(self):
        return (
            Program.objects.filter(is_published=True)
            .prefetch_related("courses")
            .order_by("order", "pk")
        )


class CourseDetailView(DetailView):
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    model = Course
    slug_field = "slug"

    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related("program")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        lessons = course.lessons.filter(is_published=True).order_by("order")
        context["lessons"] = lessons

        enrollment = None
        done_ids = set()
        if self.request.user.is_authenticated:
            enrollment = course.enrollments.filter(student=self.request.user).first()
            if enrollment:
                done_ids = set(
                    enrollment.progress.values_list("lesson_id", flat=True)
                )
        context["enrollment"] = enrollment
        context["done_lesson_ids"] = done_ids

        # Экзамены курса — если модуль exams включён
        from django.apps import apps

        if apps.is_installed("apps.exams"):
            context["exams"] = course.exams.filter(is_published=True).order_by("pk")
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    """Страница урока: доступна только записавшимся на курс."""
    template_name = "courses/lesson_detail.html"
    context_object_name = "lesson"
    pk_url_kwarg = "number"
    slug_url_kwarg = "course_slug"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(
            Course, slug=kwargs["course_slug"], is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        number = self.kwargs.get(self.pk_url_kwarg)
        lesson = self.course.lessons.filter(is_published=True, order=number).first()
        if not lesson:
            raise Http404("Урок не найден")
        return lesson

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = get_object_or_404(
            Enrollment, course=self.course, student=self.request.user
        )
        context["course"] = self.course
        context["enrollment"] = enrollment
        context["is_done"] = LessonProgress.objects.filter(
            enrollment=enrollment, lesson=self.object
        ).exists()
        context["prev_lesson"] = self.course.lessons.filter(
            is_published=True, order__lt=self.object.order
        ).order_by("-order").first()
        context["next_lesson"] = self.course.lessons.filter(
            is_published=True, order__gt=self.object.order
        ).order_by("order").first()
        return context


def enroll_view(request, slug: str):
    """Запись на курс (кнопка «Записаться» на странице курса).

    Свободный курс (is_free) записывает как «слушателя» без проверки окна
    регистрации — это отдельный вход для тех, кто хочет учиться вне основы.
    """
    if not request.user.is_authenticated:
        messages.info(request, "Сначала войдите или зарегистрируйтесь.")
        return redirect("accounts:login")

    course = get_object_or_404(Course, slug=slug, is_published=True)

    if course.is_free:
        _, created = Enrollment.objects.get_or_create(
            student=request.user, course=course,
            defaults={"status": Enrollment.Status.LISTENER},
        )
        if created:
            messages.success(
                request,
                "Вы учитесь свободно — уроки и тести курса открыты. "
                "ХалякяЛлаху тааля барака фихи!",
            )
        else:
            messages.info(request, "Вы уже проходите этот курс.")
        return redirect("courses:detail", slug=course.slug)

    if not course.registration_open:
        messages.error(request, "Регистрация на этот курс сейчас закрыта.")
        return redirect("courses:detail", slug=course.slug)

    _, created = Enrollment.objects.get_or_create(
        student=request.user, course=course,
        defaults={"status": Enrollment.Status.ACTIVE},
    )
    if created:
        messages.success(request, f"Вы записаны на курс «{course.title}». БаракаЛлаху фикум!")
    else:
        messages.info(request, "Вы уже записаны на этот курс.")
    return redirect("courses:detail", slug=course.slug)


def lesson_complete_view(request, course_slug: str, number: int):
    """Отметка «урок пройден» / снятие отметки."""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(course.lessons, order=number, is_published=True)
    enrollment = get_object_or_404(Enrollment, course=course, student=request.user)

    if request.method == "POST":
        with transaction.atomic():
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment, lesson=lesson
            )
            if not created:
                progress.delete()  # повторное нажатие — снять отметку
                messages.info(request, "Отметка снята.")
            else:
                messages.success(request, "Урок отмечен пройденным. Отлично идёте!")
    return redirect("courses:lesson", course_slug=course.slug, number=lesson.order)
