# Telegram-бот: «Тест — Какой ты тип женщины в отношениях»

MVP-бот на Python + aiogram 3 + SQLite: 15 вопросов, подсчёт результата (A/B/C/D), продажа мини-курса и админка внутри Telegram.

## Запуск локально (Windows / PowerShell)

1) Создайте виртуальное окружение и установите зависимости:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Создайте `.env` (можно скопировать из примера):

```powershell
copy .env.example .env
notepad .env
```

3) Запустите бота:

```powershell
python -m app
```

## Запуск через Docker

1) Создайте `.env`:

```bash
cp .env.example .env
```

2) Запуск:

```bash
docker compose up -d --build
```

Логи:

```bash
docker compose logs -f
```

## Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота
- `ADMIN_IDS` — список Telegram ID админов через запятую
- `DB_PATH` — путь к SQLite файлу (по умолчанию `bot.db`)
- `PARSE_MODE` — `HTML` (рекомендуется)
- `QUESTION_DELAY_SEC` — задержка между вопросами (опционально)

## Команды

- `/start` — начать/перезапустить тест
- `/admin` — админ-панель (только для ID из `ADMIN_IDS`)

