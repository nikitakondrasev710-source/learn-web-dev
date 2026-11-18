"""
[Backend] Задание 4 — Pydantic.

Структурированное приложение: разделение на модули, APIRouter,
Pydantic-модели для валидации входящих данных и формирования ответов,
кастомные валидаторы и бизнес-правила в схемах.

Запуск:
    pip install fastapi uvicorn pydantic
    uvicorn solution:app --reload
    http://127.0.0.1:8000/docs
"""

from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


# ===============================================================
# 1. Схемы Pydantic — отдельные модели на каждый сценарий
# ===============================================================

class ServiceShort(BaseModel):
    """Краткая информация об услуге (для вложенных ответов)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int


class MasterShort(BaseModel):
    """Краткая информация о мастере."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ServiceRead(ServiceShort):
    """Полная услуга."""

    duration: Annotated[int, Field(gt=0, le=480, description="Длительность, минуты")]
    category: str
    is_active: bool = True


class MasterRead(MasterShort):
    """Полный мастер."""

    specialization: str = ""
    service_ids: list[int] = Field(default_factory=list)


class AppointmentCreate(BaseModel):
    """Тело POST /appointments — с валидацией всех полей."""

    model_config = ConfigDict(str_strip_whitespace=True)

    client_name: Annotated[
        str,
        Field(min_length=2, max_length=80, description="Имя клиента"),
    ]
    client_phone: Annotated[
        str,
        Field(pattern=r"^\+7 \d{3} \d{3}-\d{2}-\d{2}$",
              description="Телефон в формате +7 900 000-00-00"),
    ]
    master_id: Annotated[int, Field(ge=1)]
    service_id: Annotated[int, Field(ge=1)]
    starts_at: datetime
    comment: Annotated[str, Field(default="", max_length=300)]
    source: Literal["site", "phone", "walk_in"] = "site"

    @field_validator("client_name")
    @classmethod
    def name_must_have_two_words(cls, value: str) -> str:
        """Требуем имя и фамилию."""
        parts = value.split()
        if len(parts) < 2:
            raise ValueError("Укажите имя и фамилию")
        return value

    @field_validator("starts_at")
    @classmethod
    def no_past_dates(cls, value: datetime) -> datetime:
        """Нельзя записаться в прошлое."""
        if value < datetime.now():
            raise ValueError("Нельзя записаться в прошлое")
        return value

    @field_validator("starts_at")
    @classmethod
    def working_hours(cls, value: datetime) -> datetime:
        """Салон работает с 09:00 до 21:00."""
        if not 9 <= value.hour < 21:
            raise ValueError("Салон работает с 09:00 до 21:00")
        return value

    @model_validator(mode="after")
    def check_comment_for_walk_in(self) -> "AppointmentCreate":
        """Для записи «с улицы» комментарий обязателен."""
        if self.source == "walk_in" and not self.comment:
            raise ValueError("Для записи с улицы нужен комментарий")
        return self


class AppointmentRead(BaseModel):
    """Ответ с записью — вычисляемые поля."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    client_phone: str
    starts_at: datetime
    ends_at: datetime
    status: str
    comment: str
    master: MasterShort
    service: ServiceShort
    price: int

    @computed_field
    @property
    def duration_minutes(self) -> int:
        """Длительность записи в минутах — считается из времён."""
        return int((self.ends_at - self.starts_at).total_seconds() // 60)

    @computed_field
    @property
    def human_time(self) -> str:
        """Человекочитаемое время."""
        return f"{self.starts_at:%d.%m.%Y в %H:%M}"


class AppointmentUpdate(BaseModel):
    """Тело PATCH /appointments/{id} — все поля необязательны."""

    starts_at: datetime | None = None
    comment: Annotated[str | None, Field(max_length=300)] = None
    status: Literal["new", "confirmed", "cancelled"] | None = None


class SlotsResponse(BaseModel):
    """Ответ со списком слотов."""

    master: MasterShort
    date: str
    slots: list[dict]
    available_count: int


# ===============================================================
# 2. Данные (в реальном проекте — из БД)
# ===============================================================

SERVICES = [
    {"id": 1, "title": "Стрижка", "price": 1500, "duration": 60,
     "category": "Стрижки", "is_active": True},
    {"id": 2, "title": "Маникюр", "price": 2000, "duration": 90,
     "category": "Ногтевой сервис", "is_active": True},
    {"id": 3, "title": "Бритьё", "price": 1000, "duration": 40,
     "category": "Барбер", "is_active": True},
]

MASTERS = [
    {"id": 1, "name": "Алиса Морозова", "specialization": "стилист",
     "service_ids": [1, 3]},
    {"id": 2, "name": "Екатерина Соколова", "specialization": "ноготочки",
     "service_ids": [2]},
]

APPOINTMENTS: list[dict] = []
_next_id = 1


# ===============================================================
# 3. Роутеры — разделение маршрутов по смыслу
# ===============================================================

services_router = APIRouter(prefix="/services", tags=["Услуги"])
masters_router = APIRouter(prefix="/masters", tags=["Мастера"])
appointments_router = APIRouter(prefix="/appointments", tags=["Записи"])


def find_by_id(items: list[dict], item_id: int, what: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{what} с id={item_id} не найден",
    )


@services_router.get("", response_model=list[ServiceRead])
def list_services(
    category: Annotated[str | None, Query(description="Фильтр по категории")] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
):
    """Список услуг с фильтрами."""
    result = [s for s in SERVICES if s["is_active"]]

    if category is not None:
        result = [s for s in result if s["category"] == category]

    if max_price is not None:
        result = [s for s in result if s["price"] <= max_price]

    return result


@services_router.get("/{service_id}", response_model=ServiceRead)
def read_service(service_id: int):
    """Одна услуга по id."""
    return find_by_id(SERVICES, service_id, "Услуга")


@masters_router.get("", response_model=list[MasterRead])
def list_masters():
    """Все мастера."""
    return MASTERS


@masters_router.get("/{master_id}", response_model=MasterRead)
def read_master(master_id: int):
    """Один мастер по id."""
    return find_by_id(MASTERS, master_id, "Мастер")


@appointments_router.get("", response_model=list[AppointmentRead])
def list_appointments(
    master_id: Annotated[int | None, Query(ge=1)] = None,
    status_filter: Annotated[
        Literal["new", "confirmed", "cancelled"] | None,
        Query(alias="status"),
    ] = None,
):
    """Список записей с фильтрами."""
    result = APPOINTMENTS

    if master_id is not None:
        result = [a for a in result if a["master"]["id"] == master_id]

    if status_filter is not None:
        result = [a for a in result if a["status"] == status_filter]

    return result


@appointments_router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(payload: AppointmentCreate):
    """Создание записи. Pydantic уже проверил все поля."""
    global _next_id

    service = find_by_id(SERVICES, payload.service_id, "Услуга")
    master = find_by_id(MASTERS, payload.master_id, "Мастер")

    if payload.service_id not in master["service_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{master['name']} не оказывает услугу «{service['title']}»",
        )

    ends_at = payload.starts_at + timedelta(minutes=service["duration"])

    # Конфликт по времени у этого мастера.
    for existing in APPOINTMENTS:
        if existing["master"]["id"] != payload.master_id:
            continue
        if existing["status"] == "cancelled":
            continue
        if existing["starts_at"] < ends_at and payload.starts_at < existing["ends_at"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"У мастера уже есть запись "
                    f"{existing['starts_at']:%H:%M}–{existing['ends_at']:%H:%M}"
                ),
            )

    appointment = {
        "id": _next_id,
        "client_name": payload.client_name,
        "client_phone": payload.client_phone,
        "starts_at": payload.starts_at,
        "ends_at": ends_at,
        "status": "new",
        "comment": payload.comment,
        "master": {"id": master["id"], "name": master["name"]},
        "service": {
            "id": service["id"],
            "title": service["title"],
            "price": service["price"],
        },
        "price": service["price"],
    }

    APPOINTMENTS.append(appointment)
    _next_id += 1

    return appointment


@appointments_router.patch("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(appointment_id: int, payload: AppointmentUpdate):
    """Частичное обновление записи."""
    appointment = find_by_id(APPOINTMENTS, appointment_id, "Запись")

    if payload.starts_at is not None:
        duration = appointment["service"]["duration"] if "duration" in appointment["service"] else 60
        appointment["starts_at"] = payload.starts_at
        appointment["ends_at"] = payload.starts_at + timedelta(minutes=duration)

    if payload.comment is not None:
        appointment["comment"] = payload.comment

    if payload.status is not None:
        appointment["status"] = payload.status

    return appointment


@appointments_router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_appointment(appointment_id: int):
    """Отмена записи (мягкое удаление — статус cancelled)."""
    appointment = find_by_id(APPOINTMENTS, appointment_id, "Запись")
    appointment["status"] = "cancelled"
    return None


# ===============================================================
# 4. Приложение
# ===============================================================

app = FastAPI(
    title="Салон «БРИТВА» — API на Pydantic",
    description=(
        "Учебный проект по лекции «Pydantic»: "
        "модульная структура, APIRouter и валидация через Pydantic."
    ),
    version="2.0.0",
)

app.include_router(services_router)
app.include_router(masters_router)
app.include_router(appointments_router)


@app.get("/", tags=["Служебное"])
def root():
    """Корневой маршрут со ссылками."""
    return {
        "service": "Салон «БРИТВА» API",
        "docs": "/docs",
        "routes": ["/services", "/masters", "/appointments"],
    }
