"""
Динамическая форма теста: строится из вопросов конкретного экзамена.

Вопросы с выбором   → радио-кнопки / чекбоксы (автопроверка)
Открытые вопросы    → текстовое поле + файл (проверяет учитель)
Имя поля: q_<id вопроса>, для файла открытого вопроса: q_<id>_file
"""
from django import forms

from apps.core.validators import ASSIGNMENT_TYPES, FileValidator

OPEN_FILE_MAX_MB = 100


def build_exam_form(exam, data=None, files=None):
    questions = exam.questions.prefetch_related("choices").order_by("order")

    fields = {}
    for question in questions:
        field_name = f"q_{question.pk}"
        common = {"label": question.text, "required": False}

        if question.q_type == question.Type.OPEN:
            fields[field_name] = forms.CharField(
                widget=forms.Textarea(attrs={"class": "input", "rows": 6}), **common
            )
            fields[f"{field_name}_file"] = forms.FileField(
                label="Файл к ответу (фото / аудио / PDF — необязательно)",
                required=False,
                validators=[FileValidator(ASSIGNMENT_TYPES, max_size_mb=OPEN_FILE_MAX_MB)],
            )
        else:
            choices = [(c.id, c.text) for c in question.choices.all()]
            if question.q_type == question.Type.MULTI:
                fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(attrs={"class": "exam-choice"}),
                    **common,
                )
            else:
                fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect(attrs={"class": "exam-choice"}),
                    **common,
                )

    form_class = type("ExamForm", (forms.BaseForm,), {"base_fields": fields})
    if data is not None:
        return form_class(data, files)
    return form_class()


def parse_answers(form, exam) -> dict:
    """Достаёт из отправленной формы словарь ответов:
    {id вопроса: {"choices": [...], "text": str, "file": файл|None}}"""
    answers = {}
    for question in exam.questions.all():
        entry = {"choices": [], "text": "", "file": None}
        value = form.cleaned_data.get(f"q_{question.pk}")

        if question.q_type == question.Type.OPEN:
            entry["text"] = (value or "").strip()
            entry["file"] = form.cleaned_data.get(f"q_{question.pk}_file")
        elif value is not None:
            entry["choices"] = [int(v) for v in (value if isinstance(value, list) else [value])]

        answers[question.id] = entry
    return answers
