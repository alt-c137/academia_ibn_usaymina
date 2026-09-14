"""
Тема оформления. Доступные виды:
  paper — «классика»: слоновая кость + изумруд + золото
  sand  — «минимал»: бежевая с арабским орнаментом
  night — «ночь»: тёмная, золото на тёмном мхe
  rose  — «роза»: нежная светлая (женская часть платформы)

Приоритет: cookie посетителя → выбор женщины-роза (авто) → настройка
админа (SiteInfo.default_theme) → .env (SITE_THEME_DEFAULT) → paper.
"""

THEMES = ("paper", "sand", "night", "rose")


class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        theme = request.COOKIES.get("theme")
        if theme not in THEMES:
            theme = None
            user = getattr(request, "user", None)
            # Женщинам по умолчанию — нежная «Роза» (свой выбор важнее)
            if user is not None and user.is_authenticated and user.gender == "female":
                theme = "rose"
            if theme is None:
                from apps.core.models import SiteInfo

                site = SiteInfo.load()
                if site is not None and site.default_theme in THEMES:
                    theme = site.default_theme
            if theme is None:
                from django.conf import settings

                theme = settings.SITE_THEME_DEFAULT
            if theme not in THEMES:
                theme = "paper"
        request.theme = theme
        return self.get_response(request)
