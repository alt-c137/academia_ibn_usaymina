"""
Мелкие теги шаблонов.

get_item — обращение к словарю по ключу внутри шаблона:
    {{ grades|get_item:enrollment.pk }}
(в шаблонном языке Django словарь[переменная] из коробки не поддерживается).
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary: dict, key):
    return dictionary.get(key) if dictionary else None
