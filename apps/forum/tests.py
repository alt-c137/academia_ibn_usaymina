"""Тесты форума: премодерация, ответы, блокировка."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.forum.models import Board, Post, Thread


def _user(email, **kw):
    return User.objects.create_user(email=email, password="pass12345", **kw)


class ForumModerationTests(TestCase):
    def setUp(self):
        self.board = Board.objects.create(name="Вопросы", slug="voprosy")
        self.student = _user("s1@t.t", first_name="Студент")
        self.teacher = _user("t1@t.t", first_name="Учитель", is_staff=True)

    def test_student_thread_is_pending_and_hidden(self):
        self.client.login(email="s1@t.t", password="pass12345")
        response = self.client.post(
            "/forum/t/new/?board=voprosy",
            {"title": "Вопрос о таубе", "body": "Как выполняется тауба?"},
            follow=True,
        )
        thread = Thread.objects.get(title="Вопрос о таубе")
        self.assertFalse(thread.is_approved)  # ждёт модерации

        # аноним/другой студент тему не видит
        self.client.logout()
        response = self.client.get(f"/forum/t/{thread.pk}/")
        self.assertEqual(response.status_code, 404)

        # автор видит свою
        self.client.login(email="s1@t.t", password="pass12345")
        response = self.client.get(f"/forum/t/{thread.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_teacher_thread_published_immediately(self):
        self.client.login(email="t1@t.t", password="pass12345")
        self.client.post(
            "/forum/t/new/?board=voprosy",
            {"title": "Правила раздела", "body": "Ассаляму алейкум ва рахматуллах"},
            follow=True,
        )
        thread = Thread.objects.get(title="Правила раздела")
        self.assertTrue(thread.is_approved)
        self.client.logout()
        response = self.client.get(f"/forum/t/{thread.pk}/")
        self.assertEqual(response.status_code, 200)  # видна всем

    def test_moderator_approves(self):
        thread = Thread.objects.create(
            board=self.board, author=self.student,
            title="На проверку", body="текст", is_approved=False,
        )
        self.client.login(email="t1@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/moderate/", {"action": "approve"})
        thread.refresh_from_db()
        self.assertTrue(thread.is_approved)

    def test_banned_user_cannot_post(self):
        self.student.banned_until = timezone.now() + timedelta(days=3)
        self.student.ban_reason = "нарушение адаба"
        self.student.save()
        thread = Thread.objects.create(
            board=self.board, author=self.teacher,
            title="Тема", body="текст", is_approved=True,
        )
        self.client.login(email="s1@t.t", password="pass12345")
        response = self.client.post(f"/forum/t/{thread.pk}/", {"body": "мой ответ"})
        self.assertEqual(Post.objects.count(), 0)  # ответ не создан

    def test_reply_in_thread(self):
        thread = Thread.objects.create(
            board=self.board, author=self.teacher,
            title="Тема", body="текст", is_approved=True,
        )
        self.client.login(email="s1@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "Полезная тема, джазакаЛлаху хайран!"})
        self.assertEqual(Post.objects.count(), 1)
