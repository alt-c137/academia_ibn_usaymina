"""Расписание онлайн-встреч."""
from django.utils import timezone
from django.views.generic import ListView

from apps.meetings.models import Meeting


class MeetingListView(ListView):
    """Все встречи: предстоящие сверху, затем прошедшие (новые в начале)."""
    template_name = "meetings/list.html"
    context_object_name = "meetings"

    def get_queryset(self):
        now = timezone.now()
        upcoming = Meeting.objects.filter(
            is_published=True, starts_at__gte=now
        ).select_related("course").order_by("starts_at")
        past = Meeting.objects.filter(
            is_published=True, starts_at__lt=now
        ).select_related("course").order_by("-starts_at")[:10]
        self.extra_context = {"upcoming": list(upcoming), "past": list(past)}
        return list(upcoming)
