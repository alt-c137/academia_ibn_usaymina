"""
Карта сайта (sitemap.xml) для поисковых систем.

Сюда попадают все публичные страницы: главная, курсы, библиотека, новости.
Кабинет, тесты и учительская в карту не включаются — они за авторизацией.
"""
from django.contrib.sitemaps import Sitemap

from apps.courses.models import Course, Program
from apps.library.models import Category, Item
from apps.news.models import Post


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["core:home", "courses:list", "news:faq", "core:contact"]

    def location(self, item):
        from django.urls import reverse

        return reverse(item)


class CourseSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Course.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else f"/courses/{obj.slug}/"


class NewsSitemap(Sitemap):
    priority = 0.6
    changefreq = "daily"

    def items(self):
        return Post.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class LibrarySitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return list(Category.objects.all())

    def location(self, obj):
        return obj.get_absolute_url()


SITEMAPS = {
    "static": StaticViewSitemap,
    "courses": CourseSitemap,
    "news": NewsSitemap,
    "library": LibrarySitemap,
}
