# VR Garage (FastAPI + SQLite + JWT Roles)

Проект переведен на серьезный backend-контур: `FastAPI` + `SQLAlchemy` + `Alembic` + `JWT` + роли (`admin/manager/viewer`) с базой `SQLite`.

## Что работает

- Многостраничный сайт:
  - `http://127.0.0.1:8000/` (приветственная страница)
  - `http://127.0.0.1:8000/catalog` (основная страница каталога + режим осмотра)
  - `http://127.0.0.1:8000/about` (страница "О нас")
  - `http://127.0.0.1:8000/faq` (страница FAQ)
  - `http://127.0.0.1:8000/contacts` (страница "Контакты")
- Админка: `http://127.0.0.1:8000/admin/index.html`
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`
- UX витрины:
  - глобальный хедер `VR Garage` с поиском и кнопкой входа,
  - hero-фото с подписью,
  - каталог карточек автомобилей,
  - переход в интерактивный режим осмотра по клику на авто.

## Структура файлов

```text
/Users/admin/Documents/Playground
├── frontend/
│   ├── pages/
│   │   ├── index.html              # Приветственная страница
│   │   ├── catalog.html            # Основная страница каталога + VR
│   │   ├── about.html              # Страница "О нас"
│   │   ├── faq.html                # Страница FAQ
│   │   └── contacts.html           # Страница "Контакты"
│   └── static/
│       ├── css/
│       │   ├── site.css            # Стили приветственной страницы
│       │   ├── catalog.css         # Стили каталога
│       │   ├── about.css           # Стили страницы "О нас"
│       │   ├── faq.css             # Стили страницы FAQ
│       │   └── contacts.css        # Стили страницы "Контакты"
│       └── js/
│           ├── catalog.js          # Логика поиска, карточек и режима осмотра
│           └── faq.js              # Логика раскрытия FAQ-аккордеона
├── api/
│   ├── app/
│   │   ├── main.py                 # Роуты страниц + API + монтирование static
│   │   ├── api/v1/                 # REST endpoints
│   │   ├── models/                 # SQLAlchemy модели
│   │   ├── schemas/                # Pydantic схемы
│   │   └── services/               # Бизнес-логика
│   └── alembic/                    # Миграции БД
├── admin/                          # Админ-панель
├── assets/
│   ├── models/                     # 3D модели
│   └── uploads/images/             # Изображения автомобилей
└── data/
    └── autovr_fastapi.sqlite3      # SQLite БД
```


## Запуск

```bash
cd /Users/admin/Documents/Playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
cd api
python -m alembic upgrade head
python -m app.scripts.bootstrap
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Админ-логин по умолчанию

- Email: `admin@autovr.local`
- Password: `admin123`

Можно переопределить перед `bootstrap`:

```bash
AUTOVR_ADMIN_EMAIL=owner@example.com AUTOVR_ADMIN_PASSWORD='StrongPass123' python -m app.scripts.bootstrap
```

## Роли

- `admin`: полный доступ.
- `manager`: управление каталогом/контентом.
- `viewer`: только чтение.

## Ключевые endpoints

- Auth:
  - `POST /api/v1/auth/login`
- Brands:
  - `GET /api/v1/brands`
  - `POST /api/v1/brands` (admin/manager)
- Cars:
  - `GET /api/v1/cars`
  - `GET /api/v1/cars?published_only=false` (admin/manager)
  - `GET /api/v1/cars/{id}`
  - `POST /api/v1/cars` (admin/manager)
  - `PATCH /api/v1/cars/{id}` (admin/manager)
  - `POST /api/v1/cars/{id}/publish` (admin/manager)
  - `POST /api/v1/cars/{id}/assets?kind=model_3d|image` (admin/manager)
  - `POST /api/v1/cars/{id}/trims` (admin/manager)
- Commerce:
  - `POST /api/v1/commerce/leads`
  - `POST /api/v1/commerce/events`
  - `GET /api/v1/commerce/analytics/funnel` (admin/manager)

## БД

По умолчанию используется:

- `data/autovr_fastapi.sqlite3`

Меняется переменной `DATABASE_URL`, например:

```bash
DATABASE_URL='sqlite:////Users/admin/Documents/Playground/data/my_autovr.sqlite3'
```

## Уведомления по заявкам (Telegram)

После отправки формы на странице `Контакты` заявка:
- сохраняется в таблицу `leads`,
- отправляется в Telegram-бот (вам).

Добавьте в `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
TELEGRAM_CHAT_ID=123456789
```

## Если видишь ошибки из скриншотов

- `NotImplementedError ... ALTER of constraints in SQLite`:
  - удалите старую неполную БД и мигрируйте заново:
  - `rm -f /Users/admin/Documents/Playground/data/autovr_fastapi.sqlite3`
  - `python -m alembic upgrade head`
- `ImportError ... typing_extensions ... anaconda3`:
  - запускается не venv, а conda/python3.10.
  - используйте только `python -m ...` после `source .venv/bin/activate`.
- `Address already in use`:
  - занятый порт 8000.
  - `lsof -i :8000` и завершите процесс, либо запустите на `--port 8001`.
