"""Логика «хадиса дня» — без крона и расписаний."""
from datetime import date

from apps.hadith.models import Hadith


def get_hadith_of_the_day():
    """Хадис дня: все опубликованные по id, индекс = день_года % количество.

    Каждый календарный день индекс сдвигается — хадис сам меняется,
    зацикливаясь по кругу. Кэша нет: выборка копеечная, честность важнее.
    """
    published = Hadith.objects.filter(is_published=True).order_by("id")
    count = published.count()
    if not count:
        return None
    index = date.today().timetuple().tm_yday % count
    return published[index]
