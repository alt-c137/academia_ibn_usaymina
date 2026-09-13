"""Формы форума: новая тема и ответ. Текст фильтруется шаблонами (без HTML)."""
from django import forms

from apps.forum.models import Post, Thread


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ("title", "body")
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "body": forms.Textarea(attrs={"class": "input", "rows": 8}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("body",)
        widgets = {"body": forms.Textarea(attrs={"class": "input", "rows": 4})}
