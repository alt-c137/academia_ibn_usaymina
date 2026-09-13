"""Формы форума: тема с настройками вопроса и ответ (с пометкой учителя)."""
from django import forms

from apps.forum.models import Post, Thread


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ("title", "body", "visibility", "who_can_answer", "allow_comments")
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "body": forms.Textarea(attrs={"class": "input", "rows": 8}),
        }
        labels = {
            "visibility": "Кто увидит вопрос",
            "who_can_answer": "Кто может отвечать",
            "allow_comments": "Разрешить комментарии к теме",
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("body", "is_official")
        widgets = {
            "body": forms.Textarea(attrs={"class": "input", "rows": 4}),
        }
        labels = {"is_official": "Официальный ответ учителя"}
