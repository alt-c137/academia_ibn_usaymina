"""Форма отправки ответа на задание."""
from django import forms

from apps.assignments.models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("text", "file")

    def __init__(self, *args, allow_file=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].widget.attrs.update({"class": "input", "rows": 8})
        if not allow_file:
            del self.fields["file"]
        else:
            self.fields["file"].widget.attrs.update({"class": "input"})
