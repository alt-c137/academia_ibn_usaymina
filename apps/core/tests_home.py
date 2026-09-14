"""Тесты главной страницы: лента, кабинет, хадис, выключатели разделов."""
from django.core.cache import cache
from django.test import TestCase

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, Program
from apps.forum.models import Board, Thread
from apps.news.models import Post as NewsPost


class HomeFeedTests(TestCase):
    def tearDown(self):
        # Настройки сайта кэшируются на час: не даём утечь в другие тесты
        cache.clear()

    def setUp(self):
        self.program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(
            program=self.program, title="Курс А", slug="kurs-a",
            status=Course.Status.ACTIVE,
        )
        self.lesson = Lesson.objects.create(course=self.course, order=1, title="Урок 1")
        NewsPost.objects.create(title="Новость Н", slug="novost-n", is_published=True)
        board = Board.objects.create(name="Раздел", slug="razdel")
        Thread.objects.create(board=board, title="Тема Т", body="текст", is_approved=True)

    def _feed_titles(self):
        html = self.client.get("/").content.decode()
        return html

    def test_feed_mixes_all_kinds(self):
        html = self._feed_titles()
        self.assertIn("Новость Н", html)
        self.assertIn("Тема Т", html)
        self.assertIn("Урок 1", html)

    def test_cabinet_card_for_logged_in(self):
        User.objects.create_user(email="home@t.t", password="pass12345", first_name="Хан")
        self.client.login(email="home@t.t", password="pass12345")
        html = self.client.get("/").content.decode()
        self.assertIn("Ваш кабинет", html)
        self.assertIn("Мои курсы", html)

    def test_cabinet_hidden_for_anonymous(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("Ваш кабинет", html)

    def test_forum_disabled_removes_from_feed_and_menu(self):
        from apps.core.models import SiteInfo

        info = SiteInfo.load()
        if info is None:
            info = SiteInfo.objects.create(site_name="A")
        info.forum_enabled = False
        info.save()
        html = self.client.get("/").content.decode()
        self.assertNotIn("Тема Т", html)
        self.assertNotIn('href="/forum/"', html)

    def test_hadith_block_on_home(self):
        from apps.hadith.models import Hadith

        Hadith.objects.create(text="Хадис для главной")
        html = self.client.get("/").content.decode()
        self.assertIn("Хадис дня", html)
        self.assertIn("Хадис для главной", html)
