"""
Пользователь платформы.

Главное отличие от стандартного пользователя Django: вход выполняется по
E-MAIL, поля «имя пользователя» (username) нет вообще. Плюс пара контактных
полей — они видны учителю в админке и помогают связаться со студентом.
"""
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from apps.core.validators import IMAGE_TYPES, FileValidator


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
    avatar = models.ImageField(
        "Аватар", upload_to="accounts/avatars/%Y/", blank=True,
        validators=[FileValidator(IMAGE_TYPES, max_size_mb=2)],
        help_text="Квадратная картинка до 2 МБ (jpg, png, webp)",
    )
    gender = models.CharField(
        "Пол", max_length=6,
        choices=[("male", "Мужской"), ("female", "Женский")],
        blank=True,
        help_text="Важно: определяет доступ к разделам (женские/мужские курсы)",
    )

    # Блокировка (бан): админ указывает срок и причину. Заблокированный
    # может входить и учиться, но не может публиковать на форуме.
    banned_until = models.DateTimeField("Заблокирован до", null=True, blank=True)
    ban_reason = models.CharField("Причина блокировки", max_length=300, blank=True)

    # Доверенное лицо: не учитель, но может отвечать на форуме там, где
    # отвечать разрешено только «учителям и доверенным». Ставит галочку админ.
    is_trusted = models.BooleanField(
        "Доверенное лицо (может отвечать на форуме)", default=False,
    )

    @property
    def initials(self) -> str:
        """Буквы для кружка-заглушки, пока аватар не загружен."""
        return (self.first_name[:1] or self.email[:1]).upper()

    @property
    def is_student(self) -> bool:
        """Зачислен ли на основную программу (не слушатель и не бросил)."""
        from apps.courses.models import Enrollment

        if not self.is_authenticated:
            return False
        return self.enrollments.exclude(
            status__in=[Enrollment.Status.DROPPED, Enrollment.Status.LISTENER]
        ).exists()

    @property
    def is_banned(self) -> bool:
        from django.utils import timezone

        return bool(self.banned_until and self.banned_until > timezone.now())


class Notification(models.Model):
    """Уведомление пользователю: проверили задание, ответ учителя и т.п."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications",
        verbose_name="Кому",
    )
    title = models.CharField("Текст", max_length=250)
    url = models.CharField("Куда перейти", max_length=300, blank=True)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Когда", auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user}: {self.title}"

    USERNAME_FIELD = "email"  # чем пользователь логинится
    REQUIRED_FIELDS = []     # при createsuperuser спрашиваем только e-mail и пароль

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        full = f"{self.last_name} {self.first_name}".strip()
        return full if full else self.email
