"""Хелпер доступа к разделам, управляемым переключателями сайта.

Меню скрывает ссылку, но и сам раздел обязан закрыться: кто-то может
ввести адрес руками. Раздел выключен, если нет записи настроек с явным
False — нет записи значит сайт ещё не настроен, работаем по умолчанию.
"""
from django.http import Http404

from apps.core.models import SiteInfo


def section_enabled(flag: str) -> bool:
    site = SiteInfo.load()
    return site is None or getattr(site, flag, True)


def require_section(flag: str):
    """Гард для dispatch: Http404, если раздел выключен в настройках."""
    if not section_enabled(flag):
        raise Http404("Этот раздел сейчас отключён.")
