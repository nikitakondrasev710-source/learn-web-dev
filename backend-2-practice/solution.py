"""
[Backend] Задание 2 — Web API на FastAPI.

REST API салона: услуги, мастера, записи.
Реализованы GET и POST, path- и query-параметры, коды ответов,
валидация тела запроса и проверка занятости слота.

Запуск:
    pip install fastapi uvicorn
    uvicorn solution:app --reload
    Открыть http://127.0.0.1:8000/docs
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Салон «БРИТВА» API",
    description="Учебный REST API: услуги, мастера и записи",
    version="1.0.0",
)


# ---------------------------------------------------------------
# Данные в памяти
# ---------------------------------------------------------------

SERVICES = [
    {"id": 1, "title": "Стрижка", "price": 1500, "duration": 60},
    {"id": 2, "title": "Маникюр", "price": 2000, "duration": 90},
    {"id": 3, "title": "Бритьё", "price": 1000, "duration": 40},
    {"id": 4, "title": "Стрижка бороды", "price": 800, "duration": 30},
]

MASTERS = [
    {"id": 1, "name": "Алиса Морозова", "service_ids": [1, 3]},
    {"id": 2, "name": "Даниил Ковалёв", "service_ids": [1, 4]},
    {"id": 3, "name": "Екатерина Соколова", "service_ids": [2]},
]

# Записи хранятся в памяти — при перезапуске исчезают.
APPOINTMENTS: list[dict] = []
_next_id = 1


# ---------------------------------------------------------------
# Схемы запросов и ответов
# ---------------------------------------------------------------

class AppointmentCreate(BaseModel):
    """Тело POST /appointments."""

    client: str = Field(min_length=2, max_length=80, description="Имя клиента")
    master_id: int = Field(ge=1, description="ID мастера")
    service_id: int = Field(ge=1, description="ID услуги")
    starts_at: datetime = Field(description="Начало записи, ISO 8601")
    comment: str = Field(default="", max_length=300)


class AppointmentRead(BaseModel):
    """Ответ с записью."""

    id: int
    client: str
    master_id: int
    master_name: str
    service_id: int
    service_title: str
    price: int
    starts_at: datetime
    ends_at: datetime
    comment: str


class SlotRead(BaseModel):
    """Свободный слот."""

    time: str
    available: bool


# ---------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------

def get_service(service_id: int) -> dict:
    for service in SERVICES:
        if service["id"] == service_id:
            return service
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Услуга {service_id} не найдена",
    )


def get_master(master_id: int) -> dict:
    for master in MASTERS:
        if master["id"] == master_id:
            return master
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Мастер {master_id} не найден",
    )


def appointment_end(start: datetime, duration: int) -> datetime:
    return start + timedelta(minutes=duration)


def find_conflict(master_id: int, start: datetime, end: datetime) -> dict | None:
    """Ищет чужую запись, пересекающуюся по времени."""
    for existing in APPOINTMENTS:
        if existing["master_id"] != master_id:
            continue
        if existing["starts_at"] < end and start < existing["ends_at"]:
            return existing
    return None


def to_read(appointment: dict) -> AppointmentRead:
    return AppointmentRead(**appointment)


# ---------------------------------------------------------------
# GET /services — список услуг
# Поддерживает фильтры: max_price, min_duration
# ---------------------------------------------------------------

@app.get("/services", response_model=list[dict], tags=["Услуги"])
def list_services(
    max_price: Annotated[int | None, Query(ge=0, description="Максимальная цена")] = None,
    min_duration: Annotated[int | None, Query(ge=0, description="Минимальная длительность, мин")] = None,
):
    result = SERVICES

    if max_price is not None:
        result = [s for s in result if s["price"] <= max_price]

    if min_duration is not None:
        result = [s for s in result if s["duration"] >= min_duration]

    return result


# ---------------------------------------------------------------
# GET /services/{service_id} — одна услуга
# ---------------------------------------------------------------

@app.get("/services/{service_id}", response_model=dict, tags=["Услуги"])
def read_service(service_id: int):
    return get_service(service_id)


# ---------------------------------------------------------------
# GET /masters — список мастеров
# GET /masters/{master_id} — один мастер
# ---------------------------------------------------------------

@app.get("/masters", response_model=list[dict], tags=["Мастера"])
def list_masters(service_id: Annotated[int | None, Query(description="Фильтр по услуге")] = None):
    if service_id is None:
        return MASTERS
    return [m for m in MASTERS if service_id in m["service_ids"]]


@app.get("/masters/{master_id}", response_model=dict, tags=["Мастера"])
def read_master(master_id: int):
    return get_master(master_id)


# ---------------------------------------------------------------
# GET /slots — свободные слоты мастера на дату
# ---------------------------------------------------------------

@app.get("/slots", response_model=list[SlotRead], tags=["Записи"])
def list_slots(
    master_id: Annotated[int, Query(ge=1)],
    date: Annotated[str, Query(description="Дата в формате ГГГГ-ММ-ДД")],
    step_minutes: Annotated[int, Query(ge=15, le=120)] = 30,
):
    get_master(master_id)

    try:
        day = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата должна быть в формате ГГГГ-ММ-ДД",
        ) from None

    working_start = day.replace(hour=9, minute=0, second=0, microsecond=0)
    working_end = day.replace(hour=21, minute=0, second=0, microsecond=0)

    slots: list[SlotRead] = []
    current = working_start

    while current < working_end:
        candidate_end = current + timedelta(minutes=step_minutes)
        busy = find_conflict(master_id, current, candidate_end) is not None
        slots.append(SlotRead(time=f"{current:%H:%M}", available=not busy))
        current = candidate_end

    return slots


# ---------------------------------------------------------------
# POST /appointments — создать запись
# ---------------------------------------------------------------

@app.post(
    "/appointments",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Записи"],
)
def create_appointment(payload: AppointmentCreate):
    global _next_id

    service = get_service(payload.service_id)
    master = get_master(payload.master_id)

    # Мастер оказывает эту услугу?
    if payload.service_id not in master["service_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Мастер {master['name']} не оказывает услугу «{service['title']}»",
        )

    # Время в рабочих часах?
    if not (9 <= payload.starts_at.hour < 21):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Запись возможна только с 09:00 до 21:00",
        )

    # Не в прошлом?
    if payload.starts_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя записаться в прошлое",
        )

    ends_at = appointment_end(payload.starts_at, service["duration"])

    # Слот свободен?
    conflict = find_conflict(payload.master_id, payload.starts_at, ends_at)
    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"У мастера уже есть запись "
                f"{conflict['starts_at']:%H:%M}–{conflict['ends_at']:%H:%M}"
            ),
        )

    appointment = {
        "id": _next_id,
        "client": payload.client,
        "master_id": payload.master_id,
        "master_name": master["name"],
        "service_id": payload.service_id,
        "service_title": service["title"],
        "price": service["price"],
        "starts_at": payload.starts_at,
        "ends_at": ends_at,
        "comment": payload.comment,
    }

    APPOINTMENTS.append(appointment)
    _next_id += 1

    return to_read(appointment)


# ---------------------------------------------------------------
# GET /appointments — список записей
# ---------------------------------------------------------------

@app.get("/appointments", response_model=list[AppointmentRead], tags=["Записи"])
def list_appointments(
    master_id: Annotated[int | None, Query(description="Фильтр по мастеру")] = None,
    date: Annotated[str | None, Query(description="Фильтр по дате ГГГГ-ММ-ДД")] = None,
):
    result = APPOINTMENTS

    if master_id is not None:
        result = [a for a in result if a["master_id"] == master_id]

    if date is not None:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Дата должна быть в формате ГГГГ-ММ-ДД",
            ) from None
        result = [a for a in result if a["starts_at"].strftime("%Y-%m-%d") == date]

    return [to_read(a) for a in result]


# ---------------------------------------------------------------
# GET /appointments/{appointment_id}
# ---------------------------------------------------------------

@app.get("/appointments/{appointment_id}", response_model=AppointmentRead, tags=["Записи"])
def read_appointment(appointment_id: int):
    for appointment in APPOINTMENTS:
        if appointment["id"] == appointment_id:
            return to_read(appointment)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Запись {appointment_id} не найдена",
    )


# ---------------------------------------------------------------
# DELETE /appointments/{appointment_id} — отмена записи
# ---------------------------------------------------------------

@app.delete(
    "/appointments/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Записи"],
)
def delete_appointment(appointment_id: int):
    for index, appointment in enumerate(APPOINTMENTS):
        if appointment["id"] == appointment_id:
            APPOINTMENTS.pop(index)
            return None
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Запись {appointment_id} не найдена",
    )
