#!/usr/bin/env python
"""Управляющий скрипт Django. Все команды запускаются через него:
python manage.py runserver | migrate | makemigrations | createsuperuser | seed_demo | test
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не найден Django. Активируйте виртуальное окружение (.venv) "
            "и выполните: pip install -r requirements/dev.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
