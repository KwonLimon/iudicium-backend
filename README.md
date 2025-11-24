# ⚖️ Iudicium Backend

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Storage-c72c48?style=for-the-badge&logo=minio&logoColor=white)

**Iudicium** — це інтелектуальна система для автоматизованого аналізу кандидатів, перевірки ризиків та генерації звітів за допомогою LLM (Gemma 3) та зовнішніх реєстрів.

Проєкт реалізовано на **FastAPI** з використанням асинхронної архітектури та мікросервісного підходу.

---

## 🚀 Основні можливості

* 📄 **Розумний парсинг файлів:** Підтримка PDF, DOCX, TXT. Витягування тексту та метаданих.
* 🧠 **AI-Аналіз (Gemma 3):**
    * Оцінка відповідності кандидата вакансії (Relevance Score).
    * Аналіз Soft та Hard Skills.
    * Виявлення брехні та невідповідностей (Trust Score).
* 🛡️ **Перевірка безпеки (OSINT / Compliance):**
    * Пошук токсичних зв'язків (РФ/РБ, підсанкційні компанії).
    * Перевірка в реєстрах **YouControl** (СБУ, Миротворець, Боржники, Корупціонери).
    * Автоматичний Kill-Switch для ризикових кандидатів.
* ☁️ **Файлове сховище:** Безпечне зберігання оригіналів резюме в **MinIO** (S3).
* 📊 **Генерація звітів:** Експорт профілю кандидата у форматах:
    * `JSON` (структуровані дані).
    * `CSV` (плоска таблиця для аналітики).
    * `DOCX` (форматований документ Word).
    * `PDF` (згенерований через HTML-шаблони).

---

## 🛠 Технічний стек

* **Мова:** Python 3.13
* **Фреймворк:** FastAPI (Async)
* **База даних:** PostgreSQL 17 (використання `JSONB` для гнучких структур).
* **ORM:** SQLAlchemy 2.0 (Asyncpg).
* **AI Engine:** Ollama (Gemma 3).
* **Storage:** MinIO (S3 Compatible).
* **Task Processing:** Asyncio (паралельна обробка файлів та запитів).
* **Reports:** Jinja2, WeasyPrint, Docxtpl, Pandas.

---

## ⚙️ Встановлення та Запуск

### Передумови
* Docker & Docker Compose
* Ollama (запущена локально або в мережі)

### 1. Клонування репозиторію
```bash
git clone [https://github.com/your-username/iudicium-backend.git](https://github.com/your-username/iudicium-backend.git)
cd iudicium-backend
```

### 2. Налаштування оточення
Створіть файл .env на основі приклад:

```bash
cp .env.example .env
```
Приклад .env:

Properties

```# --- APP ---
APP_PORT=8000

# --- POSTGRESQL ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
POSTGRES_DB=iudicium_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
# Зовнішній порт для підключення з хоста
POSTGRES_EXTERNAL_PORT=5433

# --- MINIO (S3) ---
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET=files
MINIO_API=minio:9000
MINIO_PORT=9000
MINIO_PORT_APP=9001
# Зовнішні порти
MINIO_EXTERNAL_PORT=9005
MINIO_EXTERNAL_PORT_APP=9006

# --- AI & INTEGRATIONS ---
# Адреса Ollama (для доступу з контейнера до хоста)
OLLAMA_API=[http://host.docker.internal:11434](http://host.docker.internal:11434)
AI_MODEL=gemma3
YOUCONTROL_API_KEY=your_key_here
```
3. Запуск через Docker Compose
Ця команда збере образи, застосує міграції БД та запустить сервер.

```bash
docker-compose up --build
```
Після запуску:

Swagger UI: http://localhost:8000/docs

MinIO Console: http://localhost:9006

📂 Структура проєкту
```plaintext

app/
├── api/               # Роутери (Controllers)
├── core/              # Конфігурація, Middleware, Lifespan
├── db/                # Підключення до БД, Base model
├── models/            # SQLAlchemy моделі
├── schemas/           # Pydantic схеми (DTO)
├── services/          # Бізнес-логіка
│   ├── ai_service.py       # Логіка спілкування з AI
│   ├── file_service.py     # Робота з файлами та MinIO
│   ├── export_service.py   # Генерація звітів (PDF, DOCX)
│   ├── text_extractor.py   # Парсинг тексту з файлів
│   └── risk_service.py     # Перевірка стоп-факторів
├── templates/         # Jinja2 та Docx шаблони
└── main.py            # Точка входу
```


# 🔥 Особливості реалізації
### 1. Partial Success (Частковий успіх)
Система стійка до помилок. Якщо ви завантажуєте 10 файлів, і один з них пошкоджений, а MinIO "моргнув" на іншому — система обробить 8 успішних файлів, створить профіль кандидата, а про 2 помилкові файли повідомить у полі error_files.

### 2. Hybrid Database Approach
Ми використовуємо гібридний підхід до зберігання даних.

Ключові поля (ім'я, email, статус) — у реляційних колонках (SQL).

Гнучкі дані (досвід, навички, оцінки AI) — у полі JSONB. Це дозволяє змінювати структуру аналізу без міграцій бази даних.

### 3. Безпека та "Kill Switch"
Система використовує дворівневу перевірку безпеки:


AI Context: Аналіз контексту (робота в окупованих регіонах, специфічні терміни).

API Реєстрів: Перевірка фізособи в базах розшуку та санкцій.

### 📝 Автори

Шатохін Олександр, Малецький Валерій.


