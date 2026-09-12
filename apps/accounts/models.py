"""
Пользователь платформы.

Главное отличие от стандартного пользователя Django: вход выполняется по
E-MAIL, поля «имя пользователя» (username) нет вообще. Плюс пара контактных
полей — они видны учителю в админке и помогают связаться со студентом.
"""
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserManager(UserManager):
    """Менеджер, создающий пользователей по e-mail (используется командой
    createsuperuser и формой регистрации)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Нужно указать e-mail")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # осознанно отключаем поле username — вход по e-mail
    email = models.EmailField("E-mail", unique=True)

    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=25, blank=True)
    telegram = models.CharField("Telegram (без @)", max_length=60, blank=True)

    USERNAME_FIELD = "email"  # чем пользователь логинится
    REQUIRED_FIELDS = []     # при createsuperuser спрашиваем только e-mail и пароль

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        full = f"{self.last_name} {self.first_name}".strip()
        return full if full else self.email
