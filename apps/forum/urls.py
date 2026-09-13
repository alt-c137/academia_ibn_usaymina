from django.urls import path

from apps.forum import views

app_name = "forum"

urlpatterns = [
    path("", views.ForumHomeView.as_view(), name="home"),
    path("moderation/", views.ModerationQueueView.as_view(), name="moderation"),
    path("t/new/", views.ThreadCreateView.as_view(), name="thread_new"),
    path("t/<int:pk>/comments/", views.ThreadCommentsToggleView.as_view(), name="thread_comments"),
    path("t/<int:pk>/", views.ThreadView.as_view(), name="thread"),
    path("t/<int:pk>/moderate/", views.ThreadModerateView.as_view(), name="thread_moderate"),
    path("post/<int:pk>/official/", views.PostOfficialToggleView.as_view(), name="post_official"),
    path("<slug:slug>/", views.BoardView.as_view(), name="board"),
]
