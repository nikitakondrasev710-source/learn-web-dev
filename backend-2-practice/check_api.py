"""
Автопроверка [Backend] Задание 2.

Прогоняет все эндпоинты и печатает результат.
Запуск:
    python check_api.py
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


print("=== GET /services ===")
response = client.get("/services")
check("200 OK", response.status_code == 200)
check("4 услуги", len(response.json()) == 4, response.text)

response = client.get("/services", params={"max_price": 1000})
check("фильтр max_price=1000 -> 2 услуги", len(response.json()) == 2, response.text)

response = client.get("/services/1")
check("GET /services/1 -> Стрижка", response.json()["title"] == "Стрижка")

response = client.get("/services/999")
check("GET /services/999 -> 404", response.status_code == 404)

print("\n=== GET /masters ===")
response = client.get("/masters")
check("200 OK", response.status_code == 200)
check("3 мастера", len(response.json()) == 3)

response = client.get("/masters", params={"service_id": 2})
check("мастеров на маникюр: 1", len(response.json()) == 1, response.text)

print("\n=== GET /slots ===")
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
response = client.get("/slots", params={"master_id": 1, "date": tomorrow})
check("200 OK", response.status_code == 200)
check("24 слота по 30 мин", len(response.json()) == 24, str(len(response.json())))
check("первый слот 09:00", response.json()[0]["time"] == "09:00")
check("все свободны", all(s["available"] for s in response.json()))

response = client.get("/slots", params={"master_id": 1, "date": "завтра"})
check("неверная дата -> 400", response.status_code == 400)

response = client.get("/slots", params={"master_id": 99, "date": tomorrow})
check("неизвестный мастер -> 404", response.status_code == 404)

print("\n=== POST /appointments ===")
tomorrow_dt = (datetime.now() + timedelta(days=1)).replace(
    hour=10, minute=0, second=0, microsecond=0
)
payload = {
    "client": "Никита",
    "master_id": 1,
    "service_id": 1,
    "starts_at": tomorrow_dt.isoformat(),
    "comment": "Хочу короткую стрижку",
}
response = client.post("/appointments", json=payload)
check("201 Created", response.status_code == 201, response.text)
check("id=1", response.json()["id"] == 1)
check("price=1500", response.json()["price"] == 1500)
check(
    "ends_at = starts_at + 60 мин",
    response.json()["ends_at"].startswith(
        (tomorrow_dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H")
    ),
    response.json()["ends_at"],
)

print("\n=== Конфликт времени ===")
conflict_payload = dict(payload)
conflict_payload["client"] = "Олег"
conflict_payload["starts_at"] = (tomorrow_dt + timedelta(minutes=30)).isoformat()
response = client.post("/appointments", json=conflict_payload)
check("409 Conflict", response.status_code == 409, response.text)

print("\n=== Другой мастер — свободен ===")
other_payload = dict(payload)
other_payload["client"] = "Олег"
other_payload["master_id"] = 2
other_payload["service_id"] = 4
other_payload["starts_at"] = (tomorrow_dt + timedelta(minutes=30)).isoformat()
response = client.post("/appointments", json=other_payload)
check("201 Created", response.status_code == 201, response.text)

print("\n=== Валидация ===")
bad = dict(payload)
bad["client"] = "Я"
response = client.post("/appointments", json=bad)
check("короткое имя -> 422", response.status_code == 422)

bad = dict(payload)
bad["service_id"] = 2  # Алиса не делает маникюр
response = client.post("/appointments", json=bad)
check("мастер не оказывает услугу -> 400", response.status_code == 400, response.text)

bad = dict(payload)
bad["starts_at"] = (datetime.now() - timedelta(days=1)).isoformat()
response = client.post("/appointments", json=bad)
check("запись в прошлое -> 400", response.status_code == 400)

bad = dict(payload)
bad["starts_at"] = tomorrow_dt.replace(hour=23).isoformat()
response = client.post("/appointments", json=bad)
check("вне рабочих часов -> 400", response.status_code == 400)

print("\n=== GET /appointments ===")
response = client.get("/appointments")
check("200 OK", response.status_code == 200)
check("2 записи", len(response.json()) == 2, str(len(response.json())))

response = client.get("/appointments", params={"master_id": 2})
check("фильтр по мастеру -> 1", len(response.json()) == 1)

response = client.get("/appointments", params={"date": tomorrow})
check("фильтр по дате -> 2", len(response.json()) == 2, response.text)

response = client.get("/appointments/1")
check("GET /appointments/1 -> Никита", response.json()["client"] == "Никита")

response = client.get("/appointments/999")
check("GET /appointments/999 -> 404", response.status_code == 404)

print("\n=== DELETE /appointments/1 ===")
response = client.delete("/appointments/1")
check("204 No Content", response.status_code == 204)
check("осталась 1 запись", len(client.get("/appointments").json()) == 1)

response = client.delete("/appointments/1")
check("повторное удаление -> 404", response.status_code == 404)

print("\n=== Swagger ===")
response = client.get("/docs")
check("/docs доступен", response.status_code == 200)
response = client.get("/openapi.json")
check("/openapi.json доступен", response.status_code == 200)

print(f"\nИтого: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
