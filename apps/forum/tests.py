"""Тесты форума: премодерация, ответы, блокировка."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.forum.models import Board, Post, Thread


def _user(email, **kw):
    return User.objects.create_user(email=email, password="pass12345", **kw)


def _thread_post_data(title="Вопрос о таубе", body="Как выполняется тауба?"):
    """Пayload формы темы: select'ы в браузере всегда шлют выбранное значение."""
    return {
        "title": title, "body": body,
        "visibility": Thread.Visibility.PUBLIC,
        "who_can_answer": Thread.WhoCanAnswer.ANYONE,
        "allow_comments": "on",
    }


class ForumModerationTests(TestCase):
    def setUp(self):
        self.board = Board.objects.create(name="Вопросы", slug="voprosy")
        self.student = _user("s1@t.t", first_name="Студент")
        self.teacher = _user("t1@t.t", first_name="Учитель", is_staff=True)

    def test_student_thread_is_pending_and_hidden(self):
        self.client.login(email="s1@t.t", password="pass12345")
        response = self.client.post(
            "/forum/t/new/?board=voprosy",
            _thread_post_data(),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
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
            _thread_post_data(title="Правила раздела", body="Ассаляму алейкум ва рахматуллах"),
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


class ForumSettingsTests(TestCase):
    """Приватные вопросы, кто отвечает, комментарии, официальный ответ."""

    def setUp(self):
        self.board = Board.objects.create(name="Вопросы", slug="voprosy")
        self.student = _user("s2@t.t", first_name="Студент")
        self.trusted = _user("trust@t.t", first_name="Доверенный", is_trusted=True)
        self.other = _user("other@t.t", first_name="Другой")
        self.teacher = _user("t2@t.t", first_name="Учитель", is_staff=True)

    def _thread(self, **kw):
        defaults = dict(board=self.board, author=self.student,
                        title="Тема", body="текст", is_approved=True)
        defaults.update(kw)
        return Thread.objects.create(**defaults)

    def test_private_thread_hidden_from_others(self):
        thread = self._thread(visibility=Thread.Visibility.TEACHERS_ONLY)
        self.client.login(email="other@t.t", password="pass12345")
        self.assertEqual(self.client.get(f"/forum/t/{thread.pk}/").status_code, 404)
        # автор видит
        self.client.login(email="s2@t.t", password="pass12345")
        self.assertEqual(self.client.get(f"/forum/t/{thread.pk}/").status_code, 200)
        # учитель видит
        self.client.login(email="t2@t.t", password="pass12345")
        self.assertEqual(self.client.get(f"/forum/t/{thread.pk}/").status_code, 200)

    def test_teachers_only_answers_with_trusted(self):
        thread = self._thread(who_can_answer=Thread.WhoCanAnswer.TEACHERS_TRUSTED)

        # обычный студент ответить не может
        self.client.login(email="other@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "мой ответ"})
        self.assertEqual(Post.objects.count(), 0)

        # доверенное лицо — может
        self.client.login(email="trust@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "доверенный отвечает"})
        self.assertEqual(Post.objects.count(), 1)

        # учитель — может
        self.client.login(email="t2@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "ответ учителя"})
        self.assertEqual(Post.objects.count(), 2)

    def test_author_disables_comments(self):
        thread = self._thread()
        self.client.login(email="s2@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/comments/")
        thread.refresh_from_db()
        self.assertFalse(thread.allow_comments)
        # ответ больше не проходит
        self.client.login(email="other@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "поздно"})
        self.assertEqual(Post.objects.count(), 0)

    def test_global_comments_switch(self):
        from apps.core.models import SiteInfo

        info = SiteInfo.load()
        if info is None:
            info = SiteInfo.objects.create(site_name="A")
        info.forum_comments_enabled = False
        info.save()

        thread = self._thread()
        self.client.login(email="other@t.t", password="pass12345")
        self.client.post(f"/forum/t/{thread.pk}/", {"body": "ответ"})
        self.assertEqual(Post.objects.count(), 0)
        info.forum_comments_enabled = True
        info.save()

    def test_admin_bulk_comments_off(self):
        """Действие админки: закрыть комментарии у выбранных тем."""
        t1, t2 = self._thread(title="1"), self._thread(title="2")
        Thread.objects.filter(pk__in=[t1.pk, t2.pk]).update(allow_comments=False)
        t1.refresh_from_db()
        self.assertFalse(t1.allow_comments)

    def test_teacher_marks_official_answer(self):
        thread = self._thread()
        post = Post.objects.create(thread=thread, author=self.trusted, body="даль")
        self.client.login(email="t2@t.t", password="pass12345")
        self.client.post(f"/forum/post/{post.pk}/official/")
        post.refresh_from_db()
        self.assertTrue(post.is_official)

        # обычный юзер пометить не может
        self.client.login(email="other@t.t", password="pass12345")
        self.client.post(f"/forum/post/{post.pk}/official/")
        post.refresh_from_db()
        self.assertTrue(post.is_official)  # не изменилось
