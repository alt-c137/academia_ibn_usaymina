"""Формы модуля accounts: регистрация, вход, редактирование профиля."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from apps.accounts.models import User

# --- Защита от подбора пароля ---------------------------------------------
MAX_LOGIN_FAILURES = 8        # попыток до блокировки
LOGIN_BLOCK_SECONDS = 15 * 60  # на 15 минут


def _failure_cache_key(username, request):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or \
        request.META.get("REMOTE_ADDR", "")
    from django.core.cache import cache

    return f"loginfail:{username.lower()}:{ip}"


class LoginForm(AuthenticationForm):
    """Вход по e-mail + простая защита от перебора паролей:
    после 8 неудачных попыток пара e-mail+IP блокируется на 15 минут."""

    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "input", "autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )

    def clean(self):
        from django.core.cache import cache

        key = _failure_cache_key(self.cleaned_data.get("username", ""), self.request)
        failures = cache.get(key, 0)
        if failures >= MAX_LOGIN_FAILURES:
            raise forms.ValidationError(
                "Слишком много неудачных попыток входа. Подождите 15 минут и попробуйте снова."
            )
        try:
            return super().clean()
        except forms.ValidationError:
            cache.set(key, failures + 1, LOGIN_BLOCK_SECONDS)
            raise

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        # Успешный вход — счётчик неудач сбрасываем
        from django.core.cache import cache

        if self.request:
            cache.delete(_failure_cache_key(self.cleaned_data.get("username", ""), self.request))


class RegisterForm(UserCreationForm):
    """Регистрация студента: e-mail + пароль + имя + пол.

    Пол обязателен: от него зависят доступы (женские/мужские курсы).
    """

    gender = forms.ChoiceField(
        label="Пол (укажите правильно — от этого зависит доступ к курсам)",
        choices=[("male", "Мужской"), ("female", "Женский")],
        widget=forms.Select(attrs={"class": "input"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "telegram", "gender")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class ProfileForm(UserChangeForm):
    """Редактирование профиля (пароль здесь не меняется — отдельной формой сброса)."""

    password = None  # убираем служебное поле из UserChangeForm

    class Meta:
        model = User
        fields = ("avatar", "first_name", "last_name", "gender", "email",
                  "phone", "telegram")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")
        self.fields["avatar"].widget.attrs.update(
            {"accept": "image/jpeg,image/png,image/webp"}
        )
