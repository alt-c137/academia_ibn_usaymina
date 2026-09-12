"""
Тема оформления. У каждой страницы может быть один из двух видов:
  paper — «классика» (как у hdat.sa): светлая бумажная тема
  sand  — «минимал»: бежевая тема с арабским орнаментом

Выбор хранится в cookie «theme» (живёт год). Cookie, а не только localStorage,
чтобы сервер сразу отдавал правильную тему — без мигания при загрузке.
"""


class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        theme = request.COOKIES.get("theme")
        if theme not in ("paper", "sand"):
            from django.conf import settings

            theme = settings.SITE_THEME_DEFAULT
        request.theme = theme
        return self.get_response(request)
