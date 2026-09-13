@echo off
echo Запуск сервера Академии...

:: Проверяем, существует ли виртуальное окружение
if not exist ".venv\Scripts\activate.bat" (
    echo Ошибка: Виртуальное окружение не найдено в папке .venv!
    echo Убедитесь, что вы выполнили шаги установки из README.
    pause
    exit /b
)

:: Активируем виртуальное окружение
call .venv\Scripts\activate.bat

:: Запускаем сервер Django
python manage.py runserver

:: Пауза, чтобы окно не закрылось само при ошибке
pause
