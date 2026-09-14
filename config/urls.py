"""
Главная карта адресов платформы.

Каждый модуль хранит свои адреса в собственном apps/<модуль>/urls.py и
подключается здесь одной строкой. Чтобы отключить модуль — удалите его
строку path(...) и название из INSTALLED_APPS (подробнее в README.md).
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.conf.urls.static import static
from django.urls import include, path

from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),                     # главная (лендинг), контакты
    path("accounts/", include("apps.accounts.urls")),        # регистрация, вход, сброс пароля
    path("courses/", include("apps.courses.urls")),          # курсы, уроки, запись
    path("exams/", include("apps.exams.urls")),              # тесты и экзамены
    path("assignments/", include("apps.assignments.urls")),  # отправка заданий
    path("office/", include("apps.grading.urls")),           # кабинет студента, выписка
    path("library/", include("apps.library.urls")),          # библиотека материалов
    path("books/", include("apps.books.urls")),              # продажа книг (отключаемый модуль)
    path("payments/", include("apps.payments.urls")),        # мои платежи (отключаемый модуль)
    path("hadith/", include("apps.hadith.urls")),            # хадисы (отключаемый модуль)
    path("forum/", include("apps.forum.urls")),              # форум (отключаемый модуль)
    path("teacher/", include("apps.teacher.urls")),          # учительская: проверка
    path("meetings/", include("apps.meetings.urls")),        # онлайн-встречи (созвоны)
    path("", include("apps.news.urls")),                     # новости, FAQ
    path("sitemap.xml", sitemap_view, name="sitemap"),       # карта сайта для поисковиков
]

# В режиме разработки медиа-файлы (загрузки учителя) раздаёт сам Django.
# В продакшене их отдаёт Nginx.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
