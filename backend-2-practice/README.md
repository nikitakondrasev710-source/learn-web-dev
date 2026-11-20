# [Backend] Задание 2 — Web API на FastAPI

**Решение находится в этой папке:** `backend-2-practice/`

Учебный REST API салона «БРИТВА»: услуги, мастера и записи на приём.

## Файлы

| Файл | Назначение |
|---|---|
| `solution.py` | Само приложение FastAPI: модели Pydantic, все эндпоинты, бизнес-логика и валидация |
| `check_api.py` | Автопроверка: прогоняет все эндпоинты и печатает результат (`35 passed`) |
| `.gitignore` | Служебные файлы Python |

## Запуск

```bash
pip install fastapi uvicorn

# запуск сервера
uvicorn solution:app --reload

# интерактивная документация Swagger
# http://127.0.0.1:8000/docs
```

## Автопроверка

```bash
pip install fastapi httpx
python check_api.py
```

Ожидаемый результат: `Итого: 35 passed, 0 failed`.

## Реализованные эндпоинты

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/services` | Список услуг; фильтры `max_price`, `min_duration` (query-параметры) |
| GET | `/services/{service_id}` | Одна услуга по id (path-параметр), `404` если нет |
| GET | `/masters` | Список мастеров; фильтр `service_id` |
| GET | `/masters/{master_id}` | Один мастер по id, `404` если нет |
| GET | `/slots` | Свободные слоты мастера на дату (`master_id`, `date`, `step_minutes`) |
| POST | `/appointments` | Создание записи, `201 Created` |
| GET | `/appointments` | Список записей; фильтры `master_id`, `date` |
| GET | `/appointments/{appointment_id}` | Одна запись, `404` если нет |
| DELETE | `/appointments/{appointment_id}` | Отмена записи, `204 No Content` |

## Что проверяет валидация

- **Тело запроса (Pydantic):** `client` от 2 до 80 символов, `master_id`/`service_id` ≥ 1,
  `starts_at` в формате ISO 8601, `comment` до 300 символов → при нарушении `422`.
- **Мастер оказывает услугу:** иначе `400 Bad Request`.
- **Рабочие часы салона:** запись только с 09:00 до 21:00, иначе `400`.
- **Дата в прошлом:** записаться нельзя, `400`.
- **Занятость слота:** пересечение по времени у одного мастера → `409 Conflict`.
- **Формат даты** в `/slots` и `/appointments`: только `ГГГГ-ММ-ДД`, иначе `400`.

## Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "client": "Никита",
    "master_id": 1,
    "service_id": 1,
    "starts_at": "2026-12-01T10:00:00",
    "comment": "Хочу короткую стрижку"
  }'
```

Ответ `201 Created`:

```json
{
  "id": 1,
  "client": "Никита",
  "master_id": 1,
  "master_name": "Алиса Морозова",
  "service_id": 1,
  "service_title": "Стрижка",
  "price": 1500,
  "starts_at": "2026-12-01T10:00:00",
  "ends_at": "2026-12-01T11:00:00",
  "comment": "Хочу короткую стрижку"
}
```

## Данные

Услуги, мастера и записи хранятся в памяти процесса (списки и словари Python).
Записи живут до перезапуска сервера — это учебный пример, база данных появится в задании 3.
