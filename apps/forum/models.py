"""
Форум платформы: разделы → темы → сообщения.

Правила публикации (премодерация):
  - учителя и админы публикуют сразу;
  - студенты и обычные пользователи — тема попадает в очередь модерации
    и видна остальным только после одобрения (автор видит свою тему
    с пометкой «на модерации»);
  - заблокированные (User.banned_until в будущем) не могут публиковать вовсе.
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Board(TimeStampedModel):
    """Раздел форума: «Статьи», «Вопросы и ответы», «Темы»…"""

    name = models.CharField("Название", max_length=120)
    slug = models.SlugField("Адрес (латиницей)", max_length=140, unique=True)
    description = models.CharField("Описание", max_length=300, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=1)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Раздел форума"
        verbose_name_plural = "Разделы форума"
        ordering = ("order", "pk")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("forum:board", kwargs={"slug": self.slug})

    def visible_threads_count(self) -> int:
        return self.threads.filter(is_approved=True).count()


class Thread(TimeStampedModel):
    """Тема форума: первый пост + обсуждение."""

    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="threads", verbose_name="Раздел"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="forum_threads", verbose_name="Автор",
    )
    title = models.CharField("Заголовок", max_length=250)
    body = models.TextField("Текст темы")
    is_approved = models.BooleanField("Одобрено модератором", default=False)
    is_pinned = models.BooleanField("Закреплено", default=False)
    is_closed = models.BooleanField("Закрыто для ответов", default=False)
    views = models.PositiveIntegerField("Просмотры", default=0)

    class Meta:
        verbose_name = "Тема форума"
        verbose_name_plural = "Темы форума"
        ordering = ("-is_pinned", "-updated_at")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("forum:thread", kwargs={"pk": self.pk})

    @property
    def posts_count(self) -> int:
        return self.posts.count()

    @property
    def last_activity(self):
        last = self.posts.order_by("-created_at").first()
        return last.created_at if last else self.created_at


class Post(TimeStampedModel):
    """Ответ в теме."""

    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="posts", verbose_name="Тема"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="forum_posts", verbose_name="Автор",
    )
    body = models.TextField("Текст ответа")

    class Meta:
        verbose_name = "Ответ форума"
        verbose_name_plural = "Ответы форума"
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.author or 'удалён'} в «{self.thread}»"
