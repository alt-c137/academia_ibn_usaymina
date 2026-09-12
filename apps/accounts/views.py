"""
Вход, выход и профиль хранят шаблоны Django (apps/accounts/urls.py),
поэтому здесь — только регистрация и редактирование профиля.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from apps.accounts.forms import ProfileForm, RegisterForm
from apps.accounts.models import User


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("grading:office")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # сразу входим после регистрации
        messages.success(self.request, "Добро пожаловать! Аккаунт создан.")
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user  # редактируем только себя

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)
