"""Настройки продакшена. Используются командой:
DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi
"""
import os

from .base import *  # noqa: F401,F403

DEBUG = False

# Ключ обязателен в проде: без него сайт не запустится вовсе,
# а не будет молча работать на девелоперском ключе из base.py.
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 50 or SECRET_KEY == "dev-insecure-key-change-me":
    raise RuntimeError(
        "Для продакшена задай SECRET_KEY в .env (минимум 50 символов). "
        'Сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(60))"'
    )
if not any(h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",")):
    raise RuntimeError("Для продакшена задай ALLOWED_HOSTS в .env (например: academy.example.com)")

# Сжатая статика с хэшами в именах (WhiteNoise): клиент всегда получает свежие файлы
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Дополнительные заголовки безопасности (работают за HTTPS-прокси Nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"                  # запрет встраивания сайта в iframe
SECURE_REFERRER_POLICY = "same-origin"    # не течём referer'ом на чужие сайты
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Если сайт работает за HTTPS (env SITE_HTTPS=True) — строгие cookie и HSTS.
# HSTS говорит браузеру: всегда ходить только по https, год.
if os.getenv("SITE_HTTPS", "False").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Почта через SMTP из .env
if os.getenv("EMAIL_BACKEND", "smtp").lower() == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
    EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
