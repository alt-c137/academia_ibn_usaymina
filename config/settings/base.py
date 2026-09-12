"""
Базовые настройки «Академии Ибн Усаймина» — общий фундамент для dev и prod.

Здесь перечислены модули платформы (INSTALLED_APPS). Каждый модуль —
самостоятельное приложение Django в папке apps/. Как отключить или добавить
модуль — описано в README.md, раздел «Модули».
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта (папка, где лежит manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Настройки читаются из файла .env рядом с manage.py (образец — .env.example)
load_dotenv(BASE_DIR / ".env")

# --- Безопасность -----------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = False  # включается только в dev.py
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

# --- Общее ------------------------------------------------------------------
SITE_NAME = os.getenv("SITE_NAME", "Академия Ибн Усаймина")
SITE_THEME_DEFAULT = os.getenv("SITE_THEME_DEFAULT", "paper")  # paper | sand
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")  # для robots.txt/sitemap
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Модули платформы --------------------------------------------------------
# Порядок важен только для поиска шаблонов; зависимость друг от друга описана в README.
LOCAL_APPS = [
    "apps.core",         # общее ядро: настройки сайта, тема оформления
    "apps.accounts",     # пользователи: регистрация, вход, профиль
    "apps.courses",      # программы, курсы, уроки, запись, прогресс
    "apps.exams",        # тесты и экзамены: автопроверка + ручная оценка
    "apps.assignments",  # еженедельные задания
    "apps.grading",      # итоговые оценки и академическая выписка
    "apps.library",      # библиотека материалов (PDF/аудио/видео)
    "apps.news",         # новости и вопросы-ответы (FAQ)
    "apps.teacher",      # учительская: проверка заданий и экзаменов
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    *LOCAL_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # статика без отдельного сервера
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.ThemeMiddleware",  # тема оформления из cookie
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # все шаблоны в одной папке, по подпапкам приложений
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_info",  # название сайта, контакты, меню
            ],
        },
    },
]

# --- База данных --------------------------------------------------------------
# DB_ENGINE=sqlite   — разработка (файл db.sqlite3 в корне проекта)
# DB_ENGINE=postgres — продакшен (параметры ниже)
if os.getenv("DB_ENGINE", "sqlite").lower().startswith("postgres"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "academy"),
            "USER": os.getenv("DB_USER", "academy"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- Пароли -------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"  # свой пользователь со входом по e-mail
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Куда направлять пользователя после входа / выхода
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "grading:office"  # кабинет студента (модуль grading)
LOGOUT_REDIRECT_URL = "core:home"

# --- Локализация ---------------------------------------------------------------
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# --- Статика и медиа ------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]      # исходники css/js/шрифты
STATIC_ROOT = BASE_DIR / "staticfiles"        # куда собирает collectstatic
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"               # файлы, загруженные через админку

# --- Загрузка файлов --------------------------------------------------------------
# Большие файлы пишутся во временную папку на диск, не в память.
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # буфер памяти: 10 МБ
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # небуферизованные поля: 10 МБ
FILE_UPLOAD_PERMISSIONS = 0o644                  # права на загруженные файлы

# --- Логи -----------------------------------------------------------------------------
# Ошибки пишутся в файл logs/django.log (с ротацией раз в неделю).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "when": "W6",
            "backupCount": 8,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "WARNING"},
        "django.request": {"handlers": ["file"], "level": "ERROR", "propagate": False},
    },
}

# --- Почта ----------------------------------------------------------------------
# В разработке — печать писем в консоль. В prod.py переключается на SMTP из .env.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Форматы дат ---------------------------------------------------------------
from django.conf.locale.ru import formats as ru_formats  # noqa: E402

ru_formats.DATETIME_FORMAT = "d.m.Y H:i"
ru_formats.DATE_FORMAT = "d.m.Y"
