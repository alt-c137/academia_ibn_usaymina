"""Проверки модуля встреч."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.courses.models import Course, Program
from apps.meetings.models import Meeting


class MeetingTests(TestCase):
    def setUp(self):
        program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(program=program, title="Курс", slug="kurs")

    def test_status_transitions(self):
        soon = Meeting.objects.create(
            title="Скоро", starts_at=timezone.now() + timedelta(hours=1), duration_min=60
        )
        self.assertEqual(soon.status, Meeting.Status.UPCOMING)

        live = Meeting.objects.create(
            title="Сейчас", starts_at=timezone.now() - timedelta(minutes=10), duration_min=60
        )
        self.assertEqual(live.status, Meeting.Status.LIVE)

        past = Meeting.objects.create(
            title="Было", starts_at=timezone.now() - timedelta(hours=3), duration_min=60
        )
        self.assertEqual(past.status, Meeting.Status.FINISHED)

    def test_link_hidden_before_start(self):
        early = Meeting.objects.create(
            title="Рано", starts_at=timezone.now() + timedelta(days=2), duration_min=60
        )
        self.assertFalse(early.show_link)
        soon = Meeting.objects.create(
            title="Скоро", starts_at=timezone.now() + timedelta(minutes=5), duration_min=60
        )
        self.assertTrue(soon.show_link)

    def test_list_page_renders(self):
        Meeting.objects.create(
            title="Встреча", starts_at=timezone.now() + timedelta(hours=2), duration_min=60,
            is_published=True,
        )
        response = self.client.get(reverse("meetings:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Встреча")
