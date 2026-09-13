"""Страница раздела книг: три полки — бесплатные, онлайн, продаются."""
from django.views.generic import ListView

from apps.books.models import Book


class BookListView(ListView):
    template_name = "books/list.html"
    context_object_name = "books"
    paginate_by = 24  # делим по разделам, пагинация — для больших витрин

    def get_queryset(self):
        return Book.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["books"]
        context["shelves"] = [
            {"key": "free", "title": "Бесплатные книги",
             "note": "Скачать и читать свободно — знание должно быть доступным.",
             "items": [b for b in qs if b.kind == Book.Kind.FREE]},
            {"key": "online", "title": "Онлайн-книги",
             "note": "Чтение прямо в браузере, без скачивания.",
             "items": [b for b in qs if b.kind == Book.Kind.ONLINE]},
            {"key": "paid", "title": "Продаются",
             "note": "Печатные издания — заказ и доставка.",
             "items": [b for b in qs if b.kind == Book.Kind.PAID]},
        ]
        return context
