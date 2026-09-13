"""Тесты оплат: график рассрочки и видимость счёта только его владельцу."""
from django.test import TestCase

from apps.accounts.models import User
from apps.payments.models import Installment, Invoice


class InvoiceTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="pay@t.t", password="pass12345", first_name="Платильщик"
        )
        User.objects.create_user(email="other@t.t", password="pass12345", first_name="Другой")

    def test_schedule_sums_to_total(self):
        invoice = Invoice.objects.create(
            student=self.student, title="Оплата семестра", total=1_000_000
        )
        invoice.create_schedule(3)
        parts = list(invoice.installments.all())
        self.assertEqual(len(parts), 3)
        self.assertEqual(sum(p.amount for p in parts), 1_000_000)

        parts[0].is_paid = True
        parts[0].save()
        invoice = Invoice.objects.get(pk=invoice.pk)
        self.assertEqual(invoice.paid_total, parts[0].amount)
        self.assertEqual(invoice.percent, round(parts[0].amount / 10_000))

    def test_only_owner_sees_page(self):
        Invoice.objects.create(student=self.student, title="Счёт", total=500_000)
        self.client.login(email="other@t.t", password="pass12345")
        response = self.client.get("/payments/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Счёт")

        self.client.login(email="pay@t.t", password="pass12345")
        response = self.client.get("/payments/")
        self.assertContains(response, "Счёт")
