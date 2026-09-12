"""
Валидация загружаемых файлов: разрешённые расширения + максимальный размер.

Применяется к полям моделей и форм (задания, ответы экзаменов, материалы),
чтобы в media/ нельзя было положить исполняемое или гигантский файл.
"""
import os

from django.core.exceptions import ValidationError

# Разрешённые типы по группам (расширения без точки, в нижнем регистре)
DOCUMENT_TYPES = {"pdf", "doc", "docx", "txt", "zip"}
IMAGE_TYPES = {"jpg", "jpeg", "png", "gif", "webp"}
AUDIO_TYPES = {"mp3", "m4a", "aac", "ogg", "wav"}
VIDEO_TYPES = {"mp4", "webm", "mov", "m4v"}

ASSIGNMENT_TYPES = DOCUMENT_TYPES | IMAGE_TYPES | AUDIO_TYPES | VIDEO_TYPES
LESSON_TYPES = DOCUMENT_TYPES | AUDIO_TYPES | VIDEO_TYPES | IMAGE_TYPES


class FileValidator:
    """Проверяет расширение и размер файла при загрузке.

    Использование:
        validators=[FileValidator(ASSIGNMENT_TYPES, max_size_mb=100)]
    """

    def __init__(self, allowed_extensions, max_size_mb):
        self.allowed = {ext.lower() for ext in allowed_extensions}
        self.max_size = max_size_mb * 1024 * 1024

    def deconstruct(self):
        """Чтобы миграции могли сохранить ссылку на валидатор."""
        return (
            "apps.core.validators.FileValidator",
            [],
            {
                "allowed_extensions": sorted(self.allowed),
                "max_size_mb": self.max_size // 1024 // 1024,
            },
        )

    def __eq__(self, other):
        return (
            isinstance(other, FileValidator)
            and self.allowed == other.allowed
            and self.max_size == other.max_size
        )

    def __call__(self, value):
        if not value:
            return
        ext = os.path.splitext(value.name)[1].lstrip(".").lower()
        if ext not in self.allowed:
            raise ValidationError(
                "Файлы .%(ext)s запрещены. Разрешены: %(allowed)s.",
                params={"ext": ext, "allowed": ", ".join(sorted(self.allowed))},
            )
        if value.size and value.size > self.max_size:
            raise ValidationError(
                "Файл слишком большой (%(mb).1f МБ). Максимум — %(max)s МБ.",
                params={
                    "mb": value.size / 1024 / 1024,
                    "max": self.max_size // 1024 // 1024,
                },
            )
