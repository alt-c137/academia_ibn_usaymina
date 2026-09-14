"""
Templatetag рекламы: {% show_ad "header" %} и т.д.

Локации: header / sidebar / between_posts / footer (см. AdSlot.Location).
Слот выключен или актуального креатива нет — тег ничего не выводит.
"""
from django import template

from apps.ads.models import AdSlot

register = template.Library()


@register.inclusion_tag("ads/ad_banner.html")
def show_ad(location: str):
    slot = AdSlot.objects.filter(location=location, is_active=True).first()
    return {"creative": slot.active_creative() if slot else None}
