"""Тесты учительской: доступ только у учителей."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.teacher.permissions import TEACHER_GROUP, is_teacher


class TeacherAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("student@t.local", "pass12345",
                                                first_name="Студент")
        self.staff = User.objects.create_user("teacher@t.local", "pass12345",
                                              first_name="Учитель", is_staff=True)

    def test_dashboard_denied_for_student(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("teacher:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_open_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("teacher:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_group_membership_grants_access(self):
        from django.contrib.auth.models import Group

        group, _ = Group.objects.get_or_create(name=TEACHER_GROUP)
        self.student.groups.add(group)
        self.assertTrue(is_teacher(self.student))

    def test_anonymous_redirected(self):
        response = self.client.get(reverse("teacher:dashboard"))
        self.assertEqual(response.status_code, 302)
