"""
Оплата обучения: счёт на студента + график рассрочки.

Принцип (без онлайн-кассы и договоров с платёжными системами):
  1. Админ/учитель создаёт счёт студенту: за что, сколько всего и на сколько
     частей разбить (рассрочка).
  2. Части (Installment) получают свои сроки. Студент видит график в кабинете
     и реквизиты для перевода (их задаёт админ в «Контакты сайта»).
  3. Учитель отмечает поступление галочкой — часть становится «Оплачено».

Модуль отключаемый: убрать «apps.payments» из LOCAL_APPS и строку
в config/urls.py (см. README).
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Invoice(TimeStampedModel):
    class Kind(models.TextChoices):
        ADMISSION = "admission", "Поступление (взнос)"
        TUITION = "tuition", "Обучение (семестр/курс)"
        OTHER = "other", "Другое"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="invoices", verbose_name="Студент",
    )
    kind = models.CharField("За что", max_length=12, choices=Kind.choices,
                            default=Kind.TUITION)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", verbose_name="Курс (необязательно)",
    )
    title = models.CharField("Назначение", max_length=200,
                             help_text="Например: Оплата за семестр, осень 2026")
    total = models.PositiveIntegerField("Сумма всего, сум")
    note = models.CharField("Заметка для студента", max_length=300, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Счёт на оплату"
        verbose_name_plural = "Счета на оплату"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.student} — {self.title} ({self.total} сум)"

    @property
    def paid_total(self) -> int:
        return sum(i.amount for i in self.installments.filter(is_paid=True))

    @property
    def percent(self) -> int:
        if not self.total:
            return 0
        return round(self.paid_total / self.total * 100)

    def create_schedule(self, parts: int):
        """Разбить счёт на равные части с месячным шагом (для рассрочки)."""
        from django.utils import timezone
        from datetime import timedelta

        self.installments.all().delete()
        amount = self.total // parts
        remainder = self.total - amount * parts
        now = timezone.now()
        for number in range(1, parts + 1):
            # остаток добавляем к первой части, чтобы сумма сходилась
            self.installments.create(
                number=number,
                amount=amount + (remainder if number == 1 else 0),
                due_at=now + timedelta(days=30 * (number - 1)),
            )


class Installment(models.Model):
    """Часть оплаты (платёж по графику рассрочки)."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="installments",
        verbose_name="Счёт",
    )
    number = models.PositiveSmallIntegerField("№ платежа", default=1)
    amount = models.PositiveIntegerField("Сумма, сум")
    due_at = models.DateTimeField("Оплатить до", null=True, blank=True)
    is_paid = models.BooleanField("Оплачено", default=False)
    paid_at = models.DateTimeField("Дата поступления", null=True, blank=True)
    method = models.CharField("Способ (для заметки)", max_length=80, blank=True)

    class Meta:
        verbose_name = "Платёж по графику"
        verbose_name_plural = "График платежей"
        ordering = ("invoice", "number")
        constraints = [
            models.UniqueConstraint(fields=("invoice", "number"),
                                    name="uniq_installment_number"),
        ]

    def __str__(self):
        return f"{self.invoice} — платёж {self.number}/{self.amount} сум"
