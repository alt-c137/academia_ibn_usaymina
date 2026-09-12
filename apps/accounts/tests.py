"""Тесты аккаунтов: вход по e-mail, регистрация."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthFlowTests(TestCase):
    def test_register_creates_and_logs_in(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Иса",
            "last_name": "Ташкентский",
            "email": "isa@example.com",
            "phone": "",
            "telegram": "",
            "password1": "VeryStrong123pass",
            "password2": "VeryStrong123pass",
        })
        self.assertRedirects(response, reverse("grading:office"))
        self.assertTrue(User.objects.filter(email="isa@example.com").exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_by_email(self):
        User.objects.create_user("isa@example.com", "VeryStrong123pass")
        response = self.client.post(reverse("accounts:login"), {
            "username": "isa@example.com",
            "password": "VeryStrong123pass",
        })
        self.assertRedirects(response, reverse("grading:office"))

    def test_home_page_renders(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_login_blocked_after_repeated_failures(self):
        """Защита от подбора пароля: после 8 неудач — сообщение о блокировке."""
        User.objects.create_user("brut@t.local", "VeryStrong123pass")
        for _ in range(8):
            self.client.post(reverse("accounts:login"), {
                "username": "brut@t.local",
                "password": "wrong-password",
            })
        response = self.client.post(reverse("accounts:login"), {
            "username": "brut@t.local",
            "password": "VeryStrong123pass",  # даже верный пароль — блок
        })
        self.assertContains(response, "Слишком много неудачных попыток", status_code=200)
