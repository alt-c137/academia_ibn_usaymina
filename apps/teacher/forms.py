"""Формы ручной проверки."""
from django import forms

from apps.assignments.models import Submission


class GradeSubmissionForm(forms.ModelForm):
    """Оценка ответа на задание: баллы + комментарий учителя."""

    class Meta:
        model = Submission
        fields = ("score", "feedback")
        widgets = {
            "feedback": forms.Textarea(attrs={"class": "input", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["score"].widget.attrs.update({"class": "input", "min": "0"})
        self.fields["feedback"].required = False
        self.fields["score"].required = False  # можно сохранить только комментарий

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is None:
            return None
        max_points = self.instance.assignment.max_points
        if score < 0:
            raise forms.ValidationError("Баллы не могут быть отрицательными.")
        if score > max_points:
            raise forms.ValidationError(f"Максимум за задание — {max_points}.")
        return score


class GradeAnswerForm(forms.Form):
    """Оценка открытого ответа экзамена: баллы + комментарий."""

    points = forms.DecimalField(
        label="Баллы", min_value=0, decimal_places=1, max_digits=4,
        widget=forms.NumberInput(attrs={"class": "input"}),
    )
    feedback = forms.CharField(
        label="Комментарий (необязательно)", required=False,
        widget=forms.Textarea(attrs={"class": "input", "rows": 3}),
    )
