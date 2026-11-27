"""
[Backend] Задание 1 — Основы Python.

Демонстрация базового синтаксиса Python на предметной области салона:
переменные и типы, коллекции, функции, классы (dataclass),
f-строки, обработка ошибок и работа с датами.

Запуск:
    python solution.py

На Windows консоль по умолчанию открывается в cp1251 и не умеет
печатать «₽». Поэтому stdout принудительно переводится в UTF-8.
"""

import sys

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

# Консоль Windows (cp1251) не поддерживает символ «₽» — переключаем вывод.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------
# 1. Переменные и типы
# ---------------------------------------------------------------

SALON_NAME = "БРИТВА"
OPEN_HOUR = 9          # int
CLOSE_HOUR = 21        # int
IS_OPEN_TODAY = True   # bool
RATING = 4.8           # float

print(f"Салон: {SALON_NAME}")
print(f"Часы работы: {OPEN_HOUR}:00–{CLOSE_HOUR}:00, рейтинг {RATING}")


# ---------------------------------------------------------------
# 2. Коллекции: список, словарь, множество, кортеж
# ---------------------------------------------------------------

# Список услуг — упорядоченная коллекция словарей.
services = [
    {"id": 1, "title": "Стрижка", "price": 1500, "duration": 60},
    {"id": 2, "title": "Маникюр", "price": 2000, "duration": 90},
    {"id": 3, "title": "Бритьё", "price": 1000, "duration": 40},
    {"id": 4, "title": "Стрижка бороды", "price": 800, "duration": 30},
]

print(f"\nВсего услуг: {len(services)}")

# Словарь мастеров: ключ — имя, значение — список услуг, которые он делает.
masters = {
    "Алиса Морозова": [1, 3],
    "Даниил Ковалёв": [1, 4],
    "Екатерина Соколова": [2],
}

# Множество — для быстрой проверки уникальности.
service_titles = {service["title"] for service in services}
print(f"Уникальных названий услуг: {len(service_titles)}")

# Кортеж — неизменяемая пара «открытие/закрытие».
WORKING_HOURS = (OPEN_HOUR, CLOSE_HOUR)


# ---------------------------------------------------------------
# 3. Функции
# ---------------------------------------------------------------

def find_service(service_id: int) -> dict | None:
    """Возвращает услугу по id или None, если такой нет."""
    for service in services:
        if service["id"] == service_id:
            return service
    return None


def total_price(service_ids: list[int]) -> int:
    """Суммарная стоимость набора услуг."""
    result = 0
    for service_id in service_ids:
        service = find_service(service_id)
        if service is not None:
            result += service["price"]
    return result


def masters_for_service(service_id: int) -> list[str]:
    """Кто из мастеров делает указанную услугу."""
    return [
        name for name, ids in masters.items() if service_id in ids
    ]


def format_price(amount: int) -> str:
    """1500 -> '1 500 ₽'."""
    return f"{amount:,}".replace(",", " ") + " ₽"


print("\n--- Проверка функций ---")
haircut = find_service(1)
print(f"Услуга id=1: {haircut['title']}, {format_price(haircut['price'])}")
print(f"Стрижка + маникюр: {format_price(total_price([1, 2]))}")
print(f"Стрижку делает: {', '.join(masters_for_service(1))}")
print(f"Несуществующая услуга: {find_service(99)}")


# ---------------------------------------------------------------
# 4. Классы и dataclass
# ---------------------------------------------------------------

@dataclass
class Appointment:
    """Запись клиента к мастеру."""

    client: str
    master: str
    service_id: int
    starts_at: datetime
    comment: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def service(self) -> dict:
        found = find_service(self.service_id)
        if found is None:
            raise ValueError(f"Услуга {self.service_id} не найдена")
        return found

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.service["duration"])

    @property
    def price(self) -> int:
        return self.service["price"]

    def overlaps(self, other: "Appointment") -> bool:
        """Пересекаются ли две записи по времени."""
        return self.starts_at < other.ends_at and other.starts_at < self.ends_at

    def summary(self) -> str:
        return (
            f"{self.starts_at:%d.%m.%Y %H:%M} — {self.client} "
            f"к {self.master}: {self.service['title']} ({format_price(self.price)})"
        )


# ---------------------------------------------------------------
# 5. Обработка ошибок
# ---------------------------------------------------------------

class SlotBusyError(Exception):
    """Время у мастера уже занято."""


appointments: list[Appointment] = []


def book(appointment: Appointment) -> Appointment:
    """Создаёт запись, проверяя занятость времени у мастера."""
    service = find_service(appointment.service_id)
    if service is None:
        raise SlotBusyError(f"Услуга {appointment.service_id} не найдена")

    # Мастер умеет делать эту услугу?
    if appointment.master not in masters:
        raise SlotBusyError(f"Мастер {appointment.master} не найден")

    if appointment.service_id not in masters[appointment.master]:
        raise SlotBusyError(
            f"Мастер {appointment.master} не оказывает услугу "
            f"{appointment.service['title']}"
        )

    # Время и вся длительность услуги должны помещаться в рабочий день.
    working_start = datetime.combine(
        appointment.starts_at.date(), time(WORKING_HOURS[0], 0)
    )
    working_end = datetime.combine(
        appointment.starts_at.date(), time(WORKING_HOURS[1], 0)
    )
    if appointment.starts_at < working_start or appointment.ends_at > working_end:
        raise SlotBusyError(
            "Запись должна полностью находиться в рабочих часах (09:00–21:00)"
        )

    # Не в прошлом?
    if appointment.starts_at < datetime.now():
        raise SlotBusyError("Нельзя записаться в прошлое")

    # Мастер свободен?
    for existing in appointments:
        if existing.master == appointment.master and existing.overlaps(appointment):
            raise SlotBusyError(
                f"У мастера {appointment.master} уже есть запись "
                f"{existing.starts_at:%H:%M}–{existing.ends_at:%H:%M}"
            )

    appointments.append(appointment)
    return appointment


print("\n--- Создание записей ---")

tomorrow = date.today() + timedelta(days=1)
at_10 = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
at_10_30 = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 30)

first = book(Appointment("Никита", "Алиса Морозова", 1, at_10))
print(first.summary())
print(f"Закончит в {first.ends_at:%H:%M}")

# Конфликт: Алиса занята с 10:00 до 11:00.
try:
    book(Appointment("Олег", "Алиса Морозова", 3, at_10_30))
except SlotBusyError as error:
    print(f"Ошибка (ожидаемо): {error}")

# Другой мастер — свободен.
second = book(Appointment("Олег", "Даниил Ковалёв", 4, at_10_30))
print(second.summary())

# Мастер не делает эту услугу.
try:
    book(Appointment("Пётр", "Екатерина Соколова", 1, at_10))
except SlotBusyError as error:
    print(f"Ошибка (ожидаемо): {error}")


# ---------------------------------------------------------------
# 6. Итог
# ---------------------------------------------------------------

print("\n--- Итог ---")
print(f"Записей создано: {len(appointments)}")
print(f"Общая сумма: {format_price(sum(a.price for a in appointments))}")

for number, appointment in enumerate(appointments, start=1):
    print(f"{number}. {appointment.summary()}")


# ---------------------------------------------------------------
# 7. Генератор свободных слотов (пригодится в следующих заданиях)
# ---------------------------------------------------------------

def free_slots(
    master: str,
    day: date,
    step_minutes: int = 30,
    service_id: int = 1,
) -> list[str]:
    """Возвращает свободное время мастера с учётом длительности услуги."""
    if type(step_minutes) is not int or step_minutes <= 0:
        raise ValueError("step_minutes должен быть положительным целым числом")

    if master not in masters:
        raise ValueError(f"Мастер {master} не найден")

    service = find_service(service_id)
    if service is None:
        raise ValueError(f"Услуга {service_id} не найдена")
    if service_id not in masters[master]:
        raise ValueError(f"Мастер {master} не оказывает услугу {service['title']}")

    duration = service["duration"]
    day_start = datetime.combine(day, time(WORKING_HOURS[0], 0))
    day_end = datetime.combine(day, time(WORKING_HOURS[1], 0))
    now = datetime.now()
    result = []
    current = day_start

    while current + timedelta(minutes=duration) <= day_end:
        candidate_end = current + timedelta(minutes=duration)
        is_past = day < now.date() or (day == now.date() and current < now)
        is_busy = any(
            existing.master == master
            and existing.starts_at < candidate_end
            and current < existing.ends_at
            for existing in appointments
        )
        if not is_past and not is_busy:
            result.append(f"{current:%H:%M}")
        current += timedelta(minutes=step_minutes)

    return result


print(f"\nСвободно у Алисы {tomorrow:%d.%m}: "
      f"{', '.join(free_slots('Алиса Морозова', tomorrow)) or 'нет'}")
