@echo off
chcp 65001 > nul
echo ===================================================
echo     АВТОМАТИЧЕСКИЙ ЗАПУСК ПРОЕКТА
echo ===================================================

:: 1. Проверка установки Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не установлен или не добавлен в PATH!
    echo Скачайте Python с официального сайта и при установке поставьте галочку "Add python.exe to PATH".
    pause
    exit /b
)

:: 2. Создание виртуального окружения (если его еще нет)
if not exist ".venv\Scripts\activate.bat" (
    echo [1/5] Создаю виртуальное окружение (.venv)...
    python -m venv .venv
) else (
    echo [1/5] Виртуальное окружение уже есть.
)

:: 3. Активация окружения
call .venv\Scripts\activate.bat

:: 4. Установка библиотек
echo [2/5] Проверяю и устанавливаю зависимости...
python -m pip install --upgrade pip > nul
if exist "requirements\dev.txt" (
    pip install -r requirements\dev.txt
) else if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [ВНИМАНИЕ] Файл с зависимостями не найден!
)

:: 5. Настройка файла .env
echo [3/5] Настраиваю конфигурацию (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env > nul
        echo Создан базовый файл настроек .env
    )
)

:: 6. Подготовка базы данных
echo [4/5] Применяю миграции базы данных...
python manage.py migrate

:: Пытаемся залить демо-данные (как указано в README проекта)
echo Загружаю демо-данные (если они еще не загружены)...
python manage.py seed_demo > nul 2>&1

:: 7. Запуск сервера
echo ===================================================
echo [5/5] ВСЕ ГОТОВО! СЕРВЕР ЗАПУСКАЕТСЯ...
echo Сайт будет доступен по ссылке: http://127.0.0.1:8000/
echo Админка: http://127.0.0.1:8000/admin/
echo Чтобы выключить сервер, просто закрой это окно.
echo ===================================================

python manage.py runserver

pause