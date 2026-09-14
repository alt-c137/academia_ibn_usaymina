"""Настройки для локальной разработки: python manage.py runserver."""
from .base import *  # noqa: F401,F403 — сознательно наследуем всё из base

DEBUG = True
ALLOWED_HOSTS = ['possum-dinner-feminine.ngrok-free.dev', '127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = [
    'https://ngrok-free.dev',
    'http://ngrok-free.dev',
]
# Временно убираем CSRF для презентации через ngrok
from config.settings.base import MIDDLEWARE
if 'django.middleware.csrf.CsrfViewMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('django.middleware.csrf.CsrfViewMiddleware')
