"""Страницы новостей и FAQ."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from apps.news.models import FAQ, Post


class PostListView(ListView):
    template_name = "news/news_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return (
            Post.objects.filter(is_published=True, published_at__lte=timezone.now())
            .order_by("-published_at")
        )


class PostDetailView(DetailView):
    template_name = "news/news_detail.html"
    context_object_name = "post"
    model = Post
    slug_field = "slug"

    def get_queryset(self):
        return Post.objects.filter(is_published=True, published_at__lte=timezone.now())


class FAQView(TemplateView):
    template_name = "news/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faqs"] = FAQ.objects.filter(is_published=True).order_by("order")
        return context
