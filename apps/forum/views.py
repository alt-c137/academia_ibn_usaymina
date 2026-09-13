"""
Страницы форума:

  /forum/                     — список разделов
  /forum/<slug>/              — темы раздела
  /forum/t/<pk>/              — тема с ответами (+ форма ответа)
  /forum/t/new/?board=<slug>  — создать тему
  /forum/moderation/          — очередь модерации (учителя/админы)

Премодерация: тема обычного пользователя публикуется после одобрения.
Заблокированные не публикуют ничего.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from apps.forum.forms import PostForm, ThreadForm
from apps.forum.models import Board, Post, Thread
from apps.teacher.permissions import is_moderator


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
    """Темы раздела: одобренные — всем, свои неодобренные — автору."""

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
        context["threads"] = list(threads.filter(is_approved=True))
        context["has_pending"] = False
        if user.is_authenticated:
            mine_pending = threads.filter(author=user, is_approved=False)
            context["threads"] += list(mine_pending)
            context["has_pending"] = mine_pending.exists()
        return context


class ThreadView(DetailView):
    """Тема + ответы + форма ответа (если тема открыта и юзер не в бане)."""

    template_name = "forum/thread.html"
    context_object_name = "thread"
    model = Thread

    def get_queryset(self):
        qs = Thread.objects.select_related("board", "author")
        user = self.request.user
        if user.is_authenticated and is_moderator(user):
            return qs
        if user.is_authenticated:
            return qs.filter(models.Q(is_approved=True) | models.Q(author=user))
        return qs.filter(is_approved=True)

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
        context["posts"] = self.object.posts.select_related("author").order_by("created_at")
        user = self.request.user
        context["is_moderator"] = user.is_authenticated and is_moderator(user)
        author = self.object.author
        context["author_is_moderator"] = bool(author and is_moderator(author))
        context["author_is_student"] = bool(author and author.is_student)
        context["can_reply"] = (
            user.is_authenticated
            and not self.object.is_closed
            and not user.is_banned
            and (self.object.is_approved or context["is_moderator"]
                 or self.object.author == user)
        )
        if context["can_reply"]:
            context["form"] = PostForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_closed:
            messages.error(request, "Тема закрыта для ответов.")
            return redirect(self.object.get_absolute_url())
        if request.user.is_banned:
            messages.error(
                request,
                f"Вы заблокированы до {request.user.banned_until:%d.%m.%Y}. "
                f"Причина: {request.user.ban_reason or 'не указана'}.",
            )
            return redirect(self.object.get_absolute_url())
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = self.object
            post.author = request.user
            post.save()
            messages.success(request, "Ответ опубликован.")
            return redirect(self.object.get_absolute_url() + f"#post-{post.pk}")
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
