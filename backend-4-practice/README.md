# [Backend] Задание 4 — Pydantic

Структурированное приложение на FastAPI: разделение на модули,
`APIRouter`, Pydantic-модели для валидации входящих данных
и формирования ответов, кастомные валидаторы и бизнес-правила в схемах.

## Файлы

| Файл | Что внутри |
|---|---|
| `solution.py` | Приложение целиком: схемы, валидаторы, роутеры, эндпоинты |
| `check_pydantic.py` | Автопроверка: 29 проверок через `fastapi.testclient` |

## Запуск

```bash
pip install fastapi uvicorn pydantic
uvicorn solution:app --reload
# Swagger: http://127.0.0.1:8000/docs
```

Работает без подключения к базе: данные хранятся в памяти модуля.

## Автопроверка

```bash
python check_pydantic.py
```

Ожидаемый результат: `29 passed, 0 failed`.
Сервер поднимать не нужно — тесты работают через `TestClient`.

## Структура приложения

### Схемы (Pydantic)

| Схема | Назначение |
|---|---|
| `ServiceShort` | Краткая услуга: `id`, `title` |
| `ServiceRead` | Услуга целиком: `price`, `duration` |
| `MasterShort` | Краткий мастер: `id`, `name` |
| `MasterRead` | Мастер с услугами и специализацией |
| `AppointmentCreate` | Тело `POST /appointments` |
| `AppointmentUpdate` | Тело `PATCH /appointments/{id}`: `starts_at`, `comment`, `status` — все необязательны |
| `AppointmentRead` | Ответ с записью и вычисляемыми полями |
| `SlotsResponse` | Ответ со свободными слотами |

Наследование `ServiceRead(ServiceShort)` и `MasterRead(MasterShort)`
показывает переиспользование полей вместо их дублирования.

### Кастомные валидаторы

| Где | Что проверяет |
|---|---|
| `@field_validator("client_name")` | Имя: минимум 2 буквы, без цифр, обрезка пробелов |
| `@field_validator("starts_at")` | Время не в прошлом, попадание в рабочие часы |
| `@model_validator(mode="after")` | Мастер оказывает выбранную услугу (сверка двух полей) |

### Роутеры

Приложение разбито на три `APIRouter`:

| Роутер | Префикс | Эндпоинты |
|---|---|---|
| `services_router` | `/services` | `GET ""`, `GET /{service_id}` |
| `masters_router` | `/masters` | `GET ""`, `GET /{master_id}` |
| `appointments_router` | `/appointments` | `GET ""`, `POST ""`, `PATCH /{appointment_id}`, `DELETE /{appointment_id}` |

Служебный `GET /` отдаёт имя и версию приложения.

## Что проверяет `check_pydantic.py`

- Коды ответов: `200`, `201`, `204`, `400`, `404`, `409`, `422`.
- Отказ при невалидном имени клиента.
- Отказ при записи в прошлое и вне рабочих часов.
- `PATCH` — изменение записи: `starts_at`, `comment` и `status`
  (`new` → `confirmed` → `cancelled`), все поля необязательны.
- Вычисляемые поля в ответе (`ends_at`, `price`, названия мастера и услуги).
- Наличие `/docs` и корректность `/openapi.json`.

## Отличия от `backend-2-practice`

| Что | `backend-2` | `backend-4` (этот) |
|---|---|---|
| Структура | один файл, роуты на `app` | три `APIRouter` по префиксам |
| Валидация | базовая (`Field(ge=1)` и т. п.) | плюс `field_validator`, `model_validator` |
| Изменение записи | нет | `PATCH /appointments/{id}` |
| Схемы ответов | плоские | наследование `Short` → `Read` |
