"""
Страницы форума:

  /forum/                     — список разделов
  /forum/<slug>/              — темы раздела
  /forum/t/<pk>/              — тема с ответами (+ форма ответа)
  /forum/t/new/?board=<slug>  — создать тему
  /forum/moderation/          — очередь модерации (учителя/админы)
  /forum/t/<pk>/comments/     — включить/выключить комментарии темы
                                (автор темы или модератор)
  /forum/post/<pk>/official/  — пометить/снять «ответ учителя» (модератор)

Права и фильтры:
  приватная тема (visibility=teachers) видна автору и учителям/админам;
  в темах «отвечают учителя и доверенные» отвечают is_teacher/is_trusted;
  комментарии закрываются глобально (SiteInfo.forum_comments_enabled),
  на уровне темы (allow_comments / is_closed) и для забаненных.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from apps.core.models import SiteInfo
from apps.forum.forms import PostForm, ThreadForm
from apps.forum.models import Board, Post, Thread
from apps.teacher.permissions import is_moderator


def forum_comments_open() -> bool:
    """Глобальный выключатель комментариев (нет записи — считаем включёнными)."""
    site = SiteInfo.load()
    return site is None or site.forum_comments_enabled


def can_answer(user, thread: Thread) -> bool:
    """Может ли user ответить в этой теме (без учёта формы — по правам)."""
    if not user.is_authenticated or user.is_banned:
        return False
    if thread.who_can_answer == Thread.WhoCanAnswer.TEACHERS_TRUSTED:
        return is_moderator(user) or user.is_trusted
    return True


class ForumHomeView(ListView):
    """Список разделов с числом тем и датой последней активности."""

    template_name = "forum/home.html"
    context_object_name = "boards"

    def get_queryset(self):
        return Board.objects.filter(is_published=True).annotate(
            threads_pub=Count("threads", filter=models.Q(threads__is_approved=True)),
            last_activity=Max("threads__posts__created_at"),
        )


class BoardView(DetailView):
    """Темы раздела: публичные одобренные + свои (в т.ч. на модерации)."""

    template_name = "forum/board.html"
    context_object_name = "board"
    model = Board
    slug_field = "slug"

    def get_queryset(self):
        return Board.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threads = self.object.threads.select_related("author").annotate(
            replies=Count("posts")
        )
        user = self.request.user
        visible = threads.filter(is_approved=True)
        if user.is_authenticated and is_moderator(user):
            context["threads"] = list(visible)
            context["pending_for_moderator"] = list(
                threads.filter(is_approved=False)
            )
        else:
            context["threads"] = list(visible)
            context["pending_for_moderator"] = []
            if user.is_authenticated:
                mine_pending = threads.filter(author=user, is_approved=False)
                context["threads"] += list(mine_pending)
        return context


class ThreadView(DetailView):
    """Тема + ответы + форма ответа (если разрешено)."""

    template_name = "forum/thread.html"
    context_object_name = "thread"
    model = Thread

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            # аноним: только одобренные публичные
            return Thread.objects.filter(
                is_approved=True,
            ).exclude(visibility=Thread.Visibility.TEACHERS_ONLY)
        if is_moderator(user):
            return Thread.objects.select_related("board", "author")
        # залогиненный: одобренные всем + свои любые (в т.ч. модерация/приватные)
        user_id = user.pk  # материализуем lazy-обёртку до попадания в Q
        return Thread.objects.filter(
            models.Q(is_approved=True) | models.Q(author_id=user_id)
        ).exclude(
            models.Q(visibility=Thread.Visibility.TEACHERS_ONLY)
            & ~models.Q(author_id=user_id)
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # счётчик просмотров — раз в минуту на сессию, чтобы F5 не накручивал
        if not request.session.session_key:
            request.session.create()
        key = f"forum_view:{request.session.session_key}:{self.object.pk}"
        if key not in cache:
            Thread.objects.filter(pk=self.object.pk).update(views=self.object.views + 1)
            cache.set(key, 1, 60)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.object
        user = self.request.user
        context["posts"] = thread.posts.select_related("author").order_by("created_at")
        context["is_moderator"] = user.is_authenticated and is_moderator(user)
        context["is_owner"] = user.is_authenticated and thread.author == user
        context["comments_open"] = (
            forum_comments_open()
            and thread.allow_comments
            and not thread.is_closed
        )
        context["can_reply"] = (
            user.is_authenticated
            and context["comments_open"]
            and (thread.is_approved or context["is_moderator"] or context["is_owner"])
            and can_answer(user, thread)
        )
        context["can_mark_official"] = context["is_moderator"]
        if context["can_reply"]:
            context["form"] = PostForm()
            if not is_moderator(user):
                context["form"].fields.pop("is_official")
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        thread = self.object
        user = request.user

        if thread.is_closed:
            messages.error(request, "Тема закрыта для ответов.")
            return redirect(thread.get_absolute_url())
        if not forum_comments_open():
            messages.error(request, "Комментарии на форуме сейчас отключены.")
            return redirect(thread.get_absolute_url())
        if not thread.allow_comments:
            messages.error(request, "Автор закрыл комментарии в этой теме.")
            return redirect(thread.get_absolute_url())
        if user.is_banned:
            messages.error(
                request,
                f"Вы заблокированы до {user.banned_until:%d.%m.%Y}. "
                f"Причина: {user.ban_reason or 'не указана'}.",
            )
            return redirect(thread.get_absolute_url())
        if not can_answer(user, thread):
            messages.error(
                request,
                "В этой теме отвечают только учителя и доверенные лица."
                if thread.who_can_answer == Thread.WhoCanAnswer.TEACHERS_TRUSTED
                else "Отвечать нельзя.",
            )
            return redirect(thread.get_absolute_url())

        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = user
            if not is_moderator(user):
                post.is_official = False  # пометить может только модератор
            post.save()
            messages.success(request, "Ответ опубликован.")
            return redirect(thread.get_absolute_url() + f"#post-{post.pk}")
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)


class ThreadCreateView(LoginRequiredMixin, CreateView):
    """Новая тема. Учителя/админы публикуются сразу, остальные — на модерацию."""

    template_name = "forum/thread_form.html"
    form_class = ThreadForm
    success_url = reverse_lazy("forum:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_banned:
            messages.error(
                request,
                f"Вы заблокированы до {request.user.banned_until:%d.%m.%Y} "
                "и не можете создавать темы.",
            )
            return redirect("forum:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        board = get_object_or_404(
            Board, slug=self.request.GET.get("board", ""), is_published=True
        )
        thread = form.save(commit=False)
        thread.board = board
        thread.author = self.request.user
        thread.is_approved = is_moderator(self.request.user)
        thread.save()
        if thread.is_approved:
            messages.success(self.request, "Тема опубликована.")
        else:
            messages.info(
                self.request,
                "Тема отправлена на модерацию — появится в разделе после проверки.",
            )
        return redirect(thread.get_absolute_url())


class ThreadCommentsToggleView(LoginRequiredMixin, View):
    """Автор темы или модератор включает/выключает комментарии у своей темы."""

    def post(self, request, pk: int):
        thread = get_object_or_404(Thread, pk=pk)
        if thread.author != request.user and not is_moderator(request.user):
            messages.error(request, "Менять комментарии может автор темы или модератор.")
            return redirect(thread.get_absolute_url())
        thread.allow_comments = not thread.allow_comments
        thread.save(update_fields=["allow_comments", "updated_at"])
        messages.info(
            request,
            "Комментарии отключены." if not thread.allow_comments
            else "Комментарии снова открыты.",
        )
        return redirect(thread.get_absolute_url())


class PostOfficialToggleView(LoginRequiredMixin, View):
    """Модератор помечает ответ как «официальный ответ учителя» (или снимает)."""

    def post(self, request, pk: int):
        post = get_object_or_404(Post, pk=pk)
        if not is_moderator(request.user):
            messages.error(request, "Пометку «ответ учителя» ставит модератор.")
            return redirect(post.thread.get_absolute_url())
        post.is_official = not post.is_official
        post.save(update_fields=["is_official"])
        messages.info(
            request,
            "Ответ помечен как официальный." if post.is_official
            else "Пометка «официальный ответ» снята.",
        )
        return redirect(post.thread.get_absolute_url() + f"#post-{post.pk}")


class ModerationQueueView(LoginRequiredMixin, ListView):
    """Очередь неодобренных тем (учителя и админы)."""

    template_name = "forum/moderation.html"
    context_object_name = "pending"

    def dispatch(self, request, *args, **kwargs):
        if not is_moderator(request.user):
            messages.error(request, "Модерация доступна учителям и админам.")
            return redirect("forum:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Thread.objects.filter(is_approved=False)
            .select_related("board", "author")
            .order_by("created_at")
        )


class ThreadModerateView(LoginRequiredMixin, View):
    """Действия модератора: одобрить / отклонить (удалить)."""

    def post(self, request, pk: int):
        if not is_moderator(request.user):
            messages.error(request, "Нет прав модератора.")
            return redirect("forum:home")
        thread = get_object_or_404(Thread, pk=pk)
        action = request.POST.get("action")
        if action == "approve":
            thread.is_approved = True
            thread.save(update_fields=["is_approved", "updated_at"])
            messages.success(request, f"Тема «{thread.title}» опубликована.")
        elif action == "delete":
            title = thread.title
            thread.delete()
            messages.info(request, f"Тема «{title}» удалена.")
        return redirect("forum:moderation")
