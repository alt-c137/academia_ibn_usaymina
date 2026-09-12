"""
Проверка настройки почты (нужна для сброса пароля):

    python manage.py check_email --to вас@почта.уз

Отправляет тестовое письмо и печатает, каким способом оно ушло
(в консоль при EMAIL_BACKEND=console, по SMTP — при smtp).
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Отправить тестовое письмо, чтобы проверить настройки почты"

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Адрес получателя")

    def handle(self, *args, **options):
        backend = settings.EMAIL_BACKEND.split(".")[-1]
        try:
            send_mail(
                subject="Академия Ибн Усаймина — проверка почты",
                message="Письмо работает! Сброс пароля будет приходить на этот адрес.",
                from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER or "noreply@local",
                recipient_list=[options["to"]],
                fail_silently=False,
            )
        except Exception as error:
            raise CommandError(f"Не удалось отправить: {error}") from error

        if backend == "ConsoleEmailBackend":
            self.stdout.write(self.style.WARNING(
                "Письмо выведено в КОНСОЛЬ (EMAIL_BACKEND=console). "
                "Для настоящей почты настройте SMTP в .env — см. README."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Письмо отправлено по SMTP на {options['to']} — почта настроена!"
            ))
