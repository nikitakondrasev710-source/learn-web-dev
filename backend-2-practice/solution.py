
from datetime import date as Date, datetime, time, timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="Салон «БРИТВА» API",
    description="Учебный REST API: услуги, мастера и записи",
    version="1.0.0",
)

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

APPOINTMENTS: list[dict] = []
_next_id = 1


class ServiceRead(BaseModel):
    id: int
    title: str
    price: int
    duration: int


class MasterRead(BaseModel):
    id: int
    name: str
    service_ids: list[int]


class AppointmentCreate(BaseModel):
    client: str = Field(min_length=2, max_length=80)
    master_id: int = Field(ge=1)
    service_id: int = Field(ge=1)
    starts_at: datetime
    comment: str = Field(default="", max_length=300)

    @field_validator("client")
    @classmethod
    def validate_client(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Имя клиента должно содержать минимум 2 символа")
        return value


class AppointmentRead(BaseModel):
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
    time: str
    available: bool


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


def normalize_datetime(value: datetime) -> datetime:
    return value.astimezone()


def working_hours(day: Date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time(9, 0)).astimezone()
    end = datetime.combine(day, time(21, 0)).astimezone()
    return start, end


def parse_date(value: str) -> Date:
    try:
        return Date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата должна быть в формате ГГГГ-ММ-ДД",
        ) from None


def appointment_end(start: datetime, duration: int) -> datetime:
    return start + timedelta(minutes=duration)


def find_conflict(
    master_id: int,
    start: datetime,
    end: datetime,
) -> dict | None:
    for existing in APPOINTMENTS:
        if existing["master_id"] != master_id:
            continue

        if existing["starts_at"] < end and start < existing["ends_at"]:
            return existing

    return None


def to_read(appointment: dict) -> AppointmentRead:
    return AppointmentRead(**appointment)


@app.get("/services", response_model=list[ServiceRead], tags=["Услуги"])
def list_services(
    max_price: Annotated[
        int | None,
        Query(ge=0, description="Максимальная цена"),
    ] = None,
    min_duration: Annotated[
        int | None,
        Query(ge=0, description="Минимальная длительность, мин"),
    ] = None,
):
    result = SERVICES

    if max_price is not None:
        result = [service for service in result if service["price"] <= max_price]

    if min_duration is not None:
        result = [
            service
            for service in result
            if service["duration"] >= min_duration
        ]

    return result


@app.get("/services/{service_id}", response_model=ServiceRead, tags=["Услуги"])
def read_service(service_id: int):
    return get_service(service_id)


@app.get("/masters", response_model=list[MasterRead], tags=["Мастера"])
def list_masters(
    service_id: Annotated[
        int | None,
        Query(ge=1, description="Фильтр по услуге"),
    ] = None,
):
    if service_id is None:
        return MASTERS

    return [
        master
        for master in MASTERS
        if service_id in master["service_ids"]
    ]


@app.get("/masters/{master_id}", response_model=MasterRead, tags=["Мастера"])
def read_master(master_id: int):
    return get_master(master_id)


@app.get("/slots", response_model=list[SlotRead], tags=["Записи"])
def list_slots(
    master_id: Annotated[int, Query(ge=1)],
    date: Annotated[str, Query(description="Дата в формате ГГГГ-ММ-ДД")],
    step_minutes: Annotated[int, Query(ge=15, le=120)] = 30,
    service_id: Annotated[int | None, Query(ge=1)] = None,
):
    master = get_master(master_id)
    parsed_date = parse_date(date)

    if service_id is not None:
        service = get_service(service_id)

        if service_id not in master["service_ids"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Мастер не оказывает выбранную услугу",
            )

        duration = service["duration"]
    else:
        duration = step_minutes

    working_start, working_end = working_hours(parsed_date)
    now = datetime.now().astimezone()

    slots: list[SlotRead] = []
    current = working_start

    while current + timedelta(minutes=duration) <= working_end:
        candidate_end = current + timedelta(minutes=duration)

        busy = (
            current < now
            or find_conflict(master_id, current, candidate_end) is not None
        )

        slots.append(
            SlotRead(
                time=current.strftime("%H:%M"),
                available=not busy,
            )
        )

        current += timedelta(minutes=step_minutes)

    return slots


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

    if payload.service_id not in master["service_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Мастер {master['name']} не оказывает услугу «{service['title']}»",
        )

    starts_at = normalize_datetime(payload.starts_at)
    ends_at = appointment_end(starts_at, service["duration"])

    working_start, working_end = working_hours(starts_at.date())

    if starts_at < working_start or ends_at > working_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Запись должна полностью находиться в пределах рабочего времени с 09:00 до 21:00",
        )

    if starts_at < datetime.now().astimezone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя записаться в прошлое",
        )

    conflict = find_conflict(
        payload.master_id,
        starts_at,
        ends_at,
    )

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
        "starts_at": starts_at,
        "ends_at": ends_at,
        "comment": payload.comment,
    }

    APPOINTMENTS.append(appointment)
    _next_id += 1

    return to_read(appointment)


@app.get(
    "/appointments",
    response_model=list[AppointmentRead],
    tags=["Записи"],
)
def list_appointments(
    master_id: Annotated[
        int | None,
        Query(ge=1, description="Фильтр по мастеру"),
    ] = None,
    date: Annotated[
        str | None,
        Query(description="Фильтр по дате ГГГГ-ММ-ДД"),
    ] = None,
):
    result = APPOINTMENTS

    if master_id is not None:
        result = [
            appointment
            for appointment in result
            if appointment["master_id"] == master_id
        ]

    if date is not None:
        parsed_date = parse_date(date)
        result = [
            appointment
            for appointment in result
            if appointment["starts_at"].date() == parsed_date
        ]

    return [to_read(appointment) for appointment in result]


@app.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentRead,
    tags=["Записи"],
)
def read_appointment(appointment_id: int):
    for appointment in APPOINTMENTS:
        if appointment["id"] == appointment_id:
            return to_read(appointment)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Запись {appointment_id} не найдена",
    )


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
