"""
Резервная копия базы данных одной командой:

    python manage.py backup_db

SQLite  — файл базы копируется в backups/ с датой в имени.
Postgres — выводится готовая команда pg_dump (выполнять на сервере).

Восстановление SQLite: остановить сервер, скопировать файл обратно.
"""
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создать резервную копию базы данных в папку backups/"

    def handle(self, *args, **options):
        engine = settings.DATABASES["default"]["ENGINE"]
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if engine.endswith("sqlite3"):
            source = Path(settings.DATABASES["default"]["NAME"])
            if not source.exists():
                self.stderr.write("База данных не найдена — нечего копировать.")
                return
            target = backup_dir / f"db-{stamp}.sqlite3"
            shutil.copy2(source, target)
            self.stdout.write(self.style.SUCCESS(f"Копия создана: {target}"))
        else:
            db = settings.DATABASES["default"]
            self.stdout.write(
                "PostgreSQL: выполните на сервере команду\n"
                f"  pg_dump -U {db['USER']} -h {db['HOST']} -F c "
                f"-f backups/db-{stamp}.dump {db['NAME']}\n"
                "Восстановление: pg_restore -U ... -d ... backups/db-....dump"
            )
