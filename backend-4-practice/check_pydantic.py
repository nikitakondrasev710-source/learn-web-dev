"""
Автопроверка [Backend] Задание 4 — Pydantic.

Запуск:
    python check_pydantic.py
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from solution import app

client = TestClient(app)

passed = 0
failed = 0


def check(name: str, condition: bool, extra: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  OK   {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


tomorrow = (datetime.now() + timedelta(days=1)).replace(
    hour=10, minute=0, second=0, microsecond=0
)

VALID = {
    "client_name": "Никита Кондрашев",
    "client_phone": "+7 900 123-45-67",
    "master_id": 1,
    "service_id": 1,
    "starts_at": tomorrow.isoformat(),
    "comment": "Хочу короткую стрижку",
    "source": "site",
}

print("=== Успешное создание ===")
response = client.post("/appointments", json=VALID)
check("201 Created", response.status_code == 201, response.text)
body = response.json()
check("цена из услуги", body["price"] == 1500)
check("вычисляемое duration_minutes=60", body["duration_minutes"] == 60, str(body.get("duration_minutes")))
check("вычисляемое human_time", "в 10:00" in body["human_time"], body.get("human_time"))
check("вложенный мастер", body["master"]["name"] == "Алиса Морозова")
check("вложенная услуга", body["service"]["title"] == "Стрижка")
check("статус по умолчанию new", body["status"] == "new")

print("\n=== Валидация Pydantic ===")

# 1. Одно слово в имени.
bad = dict(VALID, client_name="Никита")
response = client.post("/appointments", json=bad)
check("имя без фамилии -> 422", response.status_code == 422)
errors = response.json()["detail"]
check(
    "сообщение про имя и фамилию",
    any("имя и фамилию" in str(e) for e in errors),
    str(errors),
)

# 2. Телефон не по формату.
bad = dict(VALID, client_phone="89001234567")
response = client.post("/appointments", json=bad)
check("телефон не по формату -> 422", response.status_code == 422)

# 3. Прошлое.
bad = dict(VALID, starts_at=(datetime.now() - timedelta(days=1)).isoformat())
response = client.post("/appointments", json=bad)
check("прошлое -> 422", response.status_code == 422)

# 4. Вне рабочих часов.
bad = dict(VALID, starts_at=tomorrow.replace(hour=23).isoformat())
response = client.post("/appointments", json=bad)
check("23:00 -> 422", response.status_code == 422)

# 5. walk_in без комментария.
bad = dict(VALID, source="walk_in", comment="")
response = client.post("/appointments", json=bad)
check("walk_in без комментария -> 422", response.status_code == 422)

# 6. Мастер не делает услугу.
bad = dict(VALID, master_id=2, service_id=1)
response = client.post("/appointments", json=bad)
check("мастер не оказывает услугу -> 400", response.status_code == 400, response.text)

print("\n=== Конфликт времени ===")
conflict = dict(VALID)
conflict["client_name"] = "Олег Петров"
conflict["starts_at"] = (tomorrow + timedelta(minutes=30)).isoformat()
response = client.post("/appointments", json=conflict)
check("409 Conflict", response.status_code == 409, response.text)

print("\n=== Остальные эндпоинты ===")
response = client.get("/services")
check("GET /services -> 3", len(response.json()) == 3, response.text)

response = client.get("/services", params={"category": "Барбер"})
check("фильтр по категории -> 1", len(response.json()) == 1, response.text)

response = client.get("/services", params={"max_price": 1500})
check("max_price=1500 -> 2", len(response.json()) == 2, response.text)

response = client.get("/services/999")
check("услуга 999 -> 404", response.status_code == 404)

response = client.get("/masters")
check("GET /masters -> 2", len(response.json()) == 2)

response = client.get("/appointments", params={"status": "new"})
check("фильтр по статусу -> 1", len(response.json()) == 1, response.text)

appointment_id = body["id"]
response = client.patch(
    f"/appointments/{appointment_id}",
    json={"status": "confirmed", "comment": "Подтверждено по телефону"},
)
check("PATCH 200", response.status_code == 200)
check("статус изменился", response.json()["status"] == "confirmed")
check("комментарий изменился", response.json()["comment"] == "Подтверждено по телефону")

response = client.delete(f"/appointments/{appointment_id}")
check("DELETE 204", response.status_code == 204)

response = client.get("/appointments", params={"status": "cancelled"})
check("после отмены статус cancelled", len(response.json()) == 1)

response = client.get("/")
check("GET / 200", response.status_code == 200)

response = client.get("/openapi.json")
check("/openapi.json доступен", response.status_code == 200)
schema = response.json()
check(
    "в схеме есть вычисляемые поля",
    "duration_minutes" in str(schema),
    "нет duration_minutes",
)

print(f"\nИтого: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
