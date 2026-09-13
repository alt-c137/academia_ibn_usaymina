"""
Тема оформления. Доступные виды:
  paper — «классика»: слоновая кость + изумруд + золото
  sand  — «минимал»: бежевая с арабским орнаментом
  night — «ночь»: тёмная, золото на тёмном мхe

Выбор хранится в cookie «theme» (живёт год). Cookie, а не только localStorage,
чтобы сервер сразу отдавал правильную тему — без мигания при загрузке.
"""

THEMES = ("paper", "sand", "night")


class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        theme = request.COOKIES.get("theme")
        if theme not in THEMES:
            from django.conf import settings

            theme = settings.SITE_THEME_DEFAULT
        request.theme = theme
        return self.get_response(request)
