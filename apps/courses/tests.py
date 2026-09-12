"""Тесты курсов: запись, отметка урока, прогресс, доступ к уроку."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, LessonProgress, Program


class EnrollFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("s@t.local", "pass12345")
        program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(
            program=program, title="Курс", slug="kurs", status=Course.Status.REGISTRATION
        )
        self.lesson = Lesson.objects.create(course=self.course, order=1, title="Урок 1")

    def test_enroll_requires_login(self):
        response = self.client.get(reverse("courses:enroll", args=[self.course.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_enroll_creates_enrollment(self):
        self.client.force_login(self.student)
        self.client.get(reverse("courses:enroll", args=[self.course.slug]))
        self.assertTrue(Enrollment.objects.filter(student=self.student,
                                                  course=self.course).exists())

    def test_lesson_page_requires_enrollment(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("courses:lesson", args=[self.course.slug, 1])
        )
        self.assertEqual(response.status_code, 404)  # не записан — урока «нет»

        Enrollment.objects.create(student=self.student, course=self.course)
        response = self.client.get(
            reverse("courses:lesson", args=[self.course.slug, 1])
        )
        self.assertEqual(response.status_code, 200)

    def test_progress_toggle(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.student)
        url = reverse("courses:lesson_complete", args=[self.course.slug, 1])
        self.client.post(url)
        self.assertEqual(LessonProgress.objects.count(), 1)
        self.client.post(url)  # повтор — снятие отметки
        self.assertEqual(LessonProgress.objects.count(), 0)

    def test_enrollment_percent(self):
        Lesson.objects.create(course=self.course, order=2, title="Урок 2")
        Lesson.objects.create(course=self.course, order=3, title="Урок 3")
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        LessonProgress.objects.create(enrollment=enrollment, lesson=self.lesson)
        self.assertEqual(enrollment.lessons_done, 1)
        self.assertEqual(enrollment.percent, 33)  # 1 из 3
