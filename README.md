# Telegram-бот: «Тест — Какой ты тип женщины в отношениях»

MVP-бот на Python + aiogram 3 + SQLite: 15 вопросов, подсчёт результата (A/B/C/D), продажа мини-курса и админка внутри Telegram.

---

## 🚀 Deploy на Railway (через GitHub)

1. Запушьте этот репозиторий в GitHub.
2. На [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → выберите ваш репозиторий.
3. В разделе **Variables** добавьте:
   - `BOT_TOKEN` — токен вашего Telegram-бота (обязательно)
   - `ADMIN_IDS` — Telegram ID админов через запятую (например `123456789,987654321`)
   - `PARSE_MODE` — `HTML` (опционально, по умолчанию HTML)
   - `QUESTION_DELAY_SEC` — задержка между вопросами в сек. (опционально, по умолчанию `0.0`)
   - `DB_PATH` — путь к SQLite файлу (опционально, по умолчанию `bot.db`)
4. Railway автоматически соберёт контейнер по `Dockerfile` и запустит бота.
5. Логи смотрите во вкладке **Deployments → Logs**.

> ⚙️ Бот работает в режиме long-polling — публичный порт и домен Railway не нужны.

### ⚠️ Важно: SQLite не персистентна на Railway

Файловая система контейнера на Railway **эфемерна**. При каждом редеплое (новый коммит, рестарт сервиса, изменение переменных) файл `bot.db` **пересоздаётся с нуля**. Это значит, что сбрасываются:

- все зарегистрированные пользователи и их ответы;
- статистика и события;
- настройки админ-панели (приветственное сообщение, ссылка на канал, текст продажи) — возвращаются к дефолтам из `app/db.py`.

**Если данные нужно сохранять между деплоями**, есть два варианта:

1. **Подключить Railway Volume** — в настройках сервиса смонтировать том в `/data` и задать переменную `DB_PATH=/data/bot.db`. SQLite будет переживать редеплои.
2. **Мигрировать на PostgreSQL** — добавить Postgres-плагин в Railway и переписать `app/db.py` на `asyncpg` или `SQLAlchemy`.

---

## 🧑‍💻 Local development

### Через Python напрямую

```bash
python -m venv .venv
source .venv/bin/activate         # Linux/Mac
# .\.venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env              # и впишите BOT_TOKEN
python -m app
```

### Через Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f
```

---

## 📦 Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── __main__.py        # entrypoint: python -m app
│   ├── main.py            # запуск бота, роутинг, хендлеры
│   ├── admin.py           # админ-панель
│   ├── config.py          # загрузка .env
│   ├── content.py         # вопросы, тексты результатов
│   ├── db.py              # SQLite + миграции + дефолтные настройки
│   ├── keyboards.py       # инлайн-клавиатуры
│   └── logic.py           # подсчёт результата теста
├── Dockerfile
├── docker-compose.yml
├── railway.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Переменные окружения

| Переменная           | Обязательно | Описание                                            |
|----------------------|-------------|-----------------------------------------------------|
| `BOT_TOKEN`          | ✅          | Токен Telegram-бота от [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS`          | —           | Telegram ID админов через запятую                   |
| `DB_PATH`            | —           | Путь к SQLite файлу (по умолчанию `bot.db`)         |
| `PARSE_MODE`         | —           | `HTML` (рекомендуется)                              |
| `QUESTION_DELAY_SEC` | —           | Задержка между вопросами в секундах (например `0.4`) |

---

## 💬 Команды бота

- `/start` — начать или перезапустить тест
- `/admin` — админ-панель (доступна только пользователям из `ADMIN_IDS`)
