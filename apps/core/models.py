"""
Общие модели ядра.

TimeStampedModel — абстрактный родитель: добавляет любому объекту поля
created_at / updated_at (когда создан и когда последний раз изменён).
SiteInfo — единственная на сайт запись с контактами и текстами (правится
в админке, чтобы учитель мог менять телефон WhatsApp без помощи программиста).
"""
from django.core.cache import cache
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        abstract = True  # таблицы в БД для этого класса не создаётся


class SiteInfo(models.Model):
    """Единственная запись с контактами платформы. Создаётся командой seed_demo
    или вручную: админка → Ядро платформы → Контакты сайта → Добавить."""

    site_name = models.CharField("Название платформы", max_length=120)
    tagline = models.CharField("Краткий слоган", max_length=200, blank=True)
    whatsapp = models.CharField("WhatsApp (номер с кодом страны, без +)", max_length=20, blank=True)
    telegram = models.CharField("Telegram (имя канала или @пользователя)", max_length=60, blank=True)
    email = models.EmailField("Электронная почта", blank=True)
    about_footer = models.TextField("Текст в подвале сайта", blank=True)

    # Отправка решений через мессенджеры — резервный канал на случай,
    # когда сайт недоступен. Включает и выключает учитель/админ.
    submissions_via_messengers = models.BooleanField(
        "Показывать на заданиях отправку через WhatsApp/Telegram", default=False,
        help_text="Резервный способ сдачи решений, если сайт недоступен",
    )
    messengers_note = models.CharField(
        "Пояснение к мессенджерам", max_length=300, blank=True,
        default="Если сайт недоступен — отправьте решение учителю в мессенджер, приложив файл:",
    )

    # Раздел продажи книг (модуль apps.books). Появляется в меню и на
    # главной только когда включён здесь — решает учитель/админ.
    show_books = models.BooleanField(
        "Показывать раздел книг в меню и на главной", default=True,
    )

    # --- Глобальные включатели разделов (пункты меню + доступ по адресу) ---
    forum_enabled = models.BooleanField("Раздел «Форум» включён", default=True)
    hadith_enabled = models.BooleanField("Раздел «Хадисы» включён", default=True)
    library_enabled = models.BooleanField("Раздел «Библиотека» включён", default=True)
    stories_enabled = models.BooleanField(
        "Раздел «Истории» (заготовка на будущее)", default=False,
    )
    secular_courses_enabled = models.BooleanField(
        "Светские курсы (заготовка на будущее)", default=False,
    )

    # --- Google AdSense: один чекбокс и ID, без правок кода ---
    adsense_enabled = models.BooleanField("Показывать Google AdSense", default=False)
    adsense_client_id = models.CharField(
        "AdSense Client ID (ca-pub-…)", max_length=50, blank=True,
    )

    # Тема по умолчанию для новых посетителей (каждый потом выбирает сам)
    default_theme = models.CharField(
        "Тема по умолчанию", max_length=10, blank=True,
        choices=[("paper", "Классика"), ("sand", "Минимал"),
                 ("night", "Ночь"), ("rose", "Роза (нежная)")],
        help_text="Пусто — берётся из .env (SITE_THEME_DEFAULT)",
    )

    # Форум: глобальный выключатель комментариев. Действует на все темы;
    # отдельно комментарии можно закрыть у конкретной темы (автором или
    # в админке через выбор тем).
    forum_comments_enabled = models.BooleanField(
        "Комментарии на форуме включены (все темы)", default=True,
        help_text="Снимите галочку, чтобы закрыть комментарии во всех темах сразу",
    )

    # Оплата обучения: реквизиты видит студент в «Мои платежи» (модуль payments).
    payment_details = models.TextField(
        "Реквизиты для оплаты", blank=True,
        help_text="Номер карты/счёта, имя получателя, куда присылать чек. "
                  "Видит только сам студент на странице платежей",
    )

    # Поддержка проекта: блок в подвале сайта (помощь редакторам и т.п.)
    show_donations = models.BooleanField("Показывать блок «Поддержать проект» в подвале", default=False)
    donations_title = models.CharField("Заголовок блока поддержки", max_length=120,
                                       blank=True, default="Поддержать проект")
    donations_text = models.CharField("Текст о поддержке", max_length=300, blank=True,
                                      default="Проект существует на пожертвования. Помощь редакторам, "
                                              "переводам книг и развитию платформы — баракаЛлаху фикум.")
    donations_details = models.TextField("Реквизиты поддержки", blank=True,
                                         help_text="Карта, счёт или ссылка — по строкам")

    class Meta:
        verbose_name = "Контакты сайта"
        verbose_name_plural = "Контакты сайта"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ожидаем только одну запись; id всегда = 1.
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_info")

    @classmethod
    def load(cls) -> "SiteInfo | None":
        """Возвращает запись контактов (с кэшем на 1 час, чтобы не дёргать БД каждый запрос)."""
        info = cache.get("site_info")
        if info is None and not SiteInfo.objects.exists():
            return None
        if info is None:
            info = SiteInfo.objects.first()
            cache.set("site_info", info, 3600)
        return info
