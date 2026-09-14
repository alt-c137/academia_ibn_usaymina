"""Страницы библиотеки: список категорий, категория, редирект материала."""
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from apps.core.sections import require_section
from apps.library.models import Category, Item


class LibraryView(ListView):
    """Главный экран библиотеки: категории + последние материалы."""

    def dispatch(self, request, *args, **kwargs):
        try:
            require_section("library_enabled")
        except Http404:
            raise Http404("Библиотека сейчас отключена.")
        return super().dispatch(request, *args, **kwargs)

    template_name = "library/library.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.all().prefetch_related("items")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_items"] = Item.objects.filter(is_published=True).select_related(
            "category"
        )[:8]
        return context


class CategoryView(ListView):
    """Материалы одной категории."""

    def dispatch(self, request, *args, **kwargs):
        try:
            require_section("library_enabled")
        except Http404:
            raise Http404("Библиотека сейчас отключена.")
        return super().dispatch(request, *args, **kwargs)

    template_name = "library/category.html"
    context_object_name = "items"

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return (
            Item.objects.filter(category=self.category, is_published=True)
            .select_related("category")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["categories"] = Category.objects.all()
        return context


def item_redirect_view(request, pk):
    """Открытие материала: отдаёт файл/ссылку и засчитывает просмотр."""
    item = get_object_or_404(Item, pk=pk, is_published=True)
    Item.objects.filter(pk=item.pk).update(views=item.views + 1)
    if item.file:
        return redirect(item.file.url)
    return redirect(item.url or "/")
