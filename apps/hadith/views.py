"""Страница «Хадисы»: список всех опубликованных."""
from django.http import Http404
from django.views.generic import ListView

from apps.core.sections import require_section
from apps.hadith.models import Hadith
from apps.hadith.services import get_hadith_of_the_day


class HadithListView(ListView):
    template_name = "hadith/list.html"
    context_object_name = "hadiths"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        require_section("hadith_enabled")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Hadith.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hadith_of_the_day"] = get_hadith_of_the_day()
        return context
