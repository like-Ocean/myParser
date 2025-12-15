# Products Parser API

> Асинхронный парсер товаров с real-time уведомлениями через WebSocket и NATS message broker

***

## Описание

Это полнофункциональное веб-приложение для 
парсинга товаров с интернет-магазина **best-magazin.com** 
с автоматическим отслеживанием изменения цен и real-time 
уведомлениями для подключенных клиентов.

### Основные возможности:

- **Автоматический парсинг** — фоновая задача обновляет товары каждые 2 минуты
- **WebSocket** — мгновенные уведомления об изменениях в браузере
- **NATS Message Broker** — событийная архитектура для масштабируемости
- **Web интерфейс** — мониторинг в реальном времени
- **Docker** — полная контейнеризация
- **Swagger UI**

***

## Технологии

### Backend:
- **FastAPI**
- **SQLAlchemy 2.0**
- **Asyncpg**
- **Pydantic**
- **HTTPX**
- **BeautifulSoup4**
- **NATS.py**

### Frontend:
- **Vanilla JavaScript**
- **WebSocket API**

***

## Быстрый старт

### Предварительные требования:

- Python 3.11+
- Docker & Docker Compose
- Git

### 1️⃣ Клонирование репозитория:

```bash
git clone https://github.com/like-Ocean/myParser
cd myParser
```

### 2️⃣ Создание `.env` файла:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Environment
ENV=production

# Database
DB_NAME=myParser
DB_USER=postgres
DB_PASSWORD=root
DB_HOST=postgres
DB_PORT=5432

# Application
APP_HOST=0.0.0.0
APP_PORT=8000

# NATS
NATS_URL=nats://nats:4222

# Parser
PARSER_URL=https://best-magazin.com/apple/iphone/?sort=p.price&order=ASC&limit=360
PARSER_INTERVAL_SECONDS=300
```

### 3️⃣ Запуск через Docker:

```bash
docker-compose up -d --build
```

### 4️⃣ Проверка работы:

Откройте в браузере:

- **Web Monitor**: http://127.0.0.1:8000/monitor
- **API Docs**: http://127.0.0.1:8000/docs
- **NATS Monitoring**: http://localhost:8222

***

## Локальная разработка

### 1️⃣ Создание виртуального окружения:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 2️⃣ Установка зависимостей:

```bash
pip install -r requirements.txt
```

### 3️⃣ Запуск NATS и PostgreSQL через Docker:

```bash
docker-compose up -d postgres nats
```

### 4️⃣ Обновите `.env` для локальной разработки:

```env
DB_HOST=127.0.0.1
NATS_URL=nats://localhost:4222
APP_HOST=127.0.0.1
APP_RELOAD=True
DEBUG=true
```

### 5️⃣ Запуск приложения:

```bash
python main.py
```

***

## Web интерфейс

http://127.0.0.1:8000/monitor для доступа к панели мониторинга:

### Функции:
- Real-time подключение к WebSocket
- Статистика сообщений
- Уведомления о создании/обновлении товаров
- Отдельная панель для NATS событий
- Кнопка запуска парсера
- Ping проверка соединения

***

## Docker

### Команды:

```bash
# Запустить все
docker-compose up -d

# Посмотреть логи
docker-compose logs -f fastapi

# Остановить
docker-compose down

# Пересобрать
docker-compose up -d --build

# Очистить включая volumes
docker-compose down -v
```

***