"""Тесты рекламы: слот выключен/активен, окно дат, темплейт-тег."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.ads.models import AdCreative, AdSlot


class AdsTests(TestCase):
    def setUp(self):
        self.slot = AdSlot.objects.create(location="header", name="Шапка")

    def _creative(self, **kw):
        defaults = dict(slot=self.slot, advertiser_name="Тест", is_active=True)
        defaults.update(kw)
        return AdCreative.objects.create(**defaults)

    def test_page_shows_active_banner(self):
        self._creative(image="ads/images/x.png")
        html = self.client.get("/").content.decode()
        self.assertIn("ad-banner", html)

    def test_inactive_creative_hidden(self):
        self._creative(image="ads/images/x.png", is_active=False)
        html = self.client.get("/").content.decode()
        self.assertNotIn("ad-banner", html)

    def test_expired_creative_hidden(self):
        today = timezone.localdate()
        self._creative(starts_at=today - timedelta(days=10),
                       ends_at=today - timedelta(days=1))
        html = self.client.get("/").content.decode()
        self.assertNotIn("ad-banner", html)

    def test_upcoming_creative_hidden(self):
        today = timezone.localdate()
        self._creative(starts_at=today + timedelta(days=5))
        html = self.client.get("/").content.decode()
        self.assertNotIn("ad-banner", html)

    def test_inactive_slot_hidden(self):
        self.slot.is_active = False
        self.slot.save()
        self._creative()
        html = self.client.get("/").content.decode()
        self.assertNotIn("ad-banner", html)
