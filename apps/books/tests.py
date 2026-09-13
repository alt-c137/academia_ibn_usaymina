"""Тесты модуля книг: страница открывается, выключатель в админке прячет раздел."""
from django.test import TestCase

from apps.core.models import SiteInfo


class BooksPageTests(TestCase):
    def test_page_renders(self):
        response = self.client.get("/books/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Наши книги")

    def test_toggle_hides_nav_link(self):
        info = SiteInfo.load()
        if info is None:
            info = SiteInfo.objects.create(site_name="Академия")
        info.show_books = False
        info.save()
        response = self.client.get("/books/")
        self.assertEqual(response.status_code, 200)  # страница жива
        self.assertNotContains(response, 'href="/books/">Книги</a>')
        info.show_books = True
        info.save()
