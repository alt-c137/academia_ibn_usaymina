"""Тесты хадисов: день меняется по дню года, страница, выключатель."""
from datetime import date

from django.test import TestCase

from apps.core.models import SiteInfo
from apps.hadith.models import Hadith
from apps.hadith.services import get_hadith_of_the_day


class HadithTests(TestCase):
    def tearDown(self):
        from django.core.cache import cache

        cache.clear()  # тест меняет SiteInfo — не уносить кэш дальше

    def setUp(self):
        for i in range(1, 4):
            Hadith.objects.create(text=f"Хадис номер {i}")

    def test_rotation_follows_day_of_year(self):
        h = get_hadith_of_the_day()
        expected = Hadith.objects.order_by("id")[date.today().timetuple().tm_yday % 3]
        self.assertEqual(h.pk, expected.pk)

    def test_unpublished_not_used(self):
        Hadith.objects.all().update(is_published=False)
        self.assertIsNone(get_hadith_of_the_day())

    def test_page_lists(self):
        response = self.client.get("/hadith/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Хадис номер 1")

    def test_section_switch_hides_page(self):
        info = SiteInfo.load()
        if info is None:
            info = SiteInfo.objects.create(site_name="A")
        info.hadith_enabled = False
        info.save()
        response = self.client.get("/hadith/")
        self.assertEqual(response.status_code, 404)
