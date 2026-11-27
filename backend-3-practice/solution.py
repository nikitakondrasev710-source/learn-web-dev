from __future__ import annotations

import argparse
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    case,
    create_engine,
    event,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PROJECT_DIR / "salon.db"


class Base(DeclarativeBase):
    pass


master_services = Table(
    "master_services",
    Base.metadata,
    Column("master_id", ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    services: Mapped[list[Service]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Service.title",
    )


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_services_price_nonnegative"),
        CheckConstraint("duration > 0", name="ck_services_duration_positive"),
        Index("ix_services_category_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)

    category: Mapped[Category] = relationship(back_populates="services")
    masters: Mapped[list[Master]] = relationship(
        secondary=master_services, back_populates="services", order_by="Master.name"
    )
    appointments: Mapped[list[Appointment]] = relationship(back_populates="service")


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    services: Mapped[list[Service]] = relationship(
        secondary=master_services, back_populates="masters", order_by="Service.title"
    )
    appointments: Mapped[list[Appointment]] = relationship(back_populates="master")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_appointments_end_after_start"),
        CheckConstraint(
            "status IN ('booked', 'completed', 'cancelled')",
            name="ck_appointments_status_valid",
        ),
        Index("ix_appointments_master_starts_at", "master_id", "starts_at"),
        Index("ix_appointments_service_id", "service_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(80), nullable=False)
    master_id: Mapped[int] = mapped_column(
        ForeignKey("masters.id", ondelete="RESTRICT"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="booked")

    master: Mapped[Master] = relationship(back_populates="appointments")
    service: Mapped[Service] = relationship(back_populates="appointments")


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}")


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    options: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}

    database_engine = create_engine(url, **options)

    if url.startswith("sqlite"):
        @event.listens_for(database_engine, "connect")
        def enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


engine = build_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=Session
)


def normalize_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def working_hours(day: date) -> tuple[datetime, datetime]:
    return datetime.combine(day, time(9, 0)), datetime.combine(day, time(21, 0))


def seed_data(session: Session) -> None:
    if session.scalar(select(func.count(Category.id))) > 0:
        return

    cutting = Category(title="Стрижки")
    beard = Category(title="Борода и бритьё")
    care = Category(title="Уход")

    services = [
        Service(title="Мужская стрижка", price=1500, duration=60, category=cutting),
        Service(title="Детская стрижка", price=1200, duration=45, category=cutting),
        Service(title="Стрижка бороды", price=800, duration=30, category=beard),
        Service(title="Классическое бритьё", price=1000, duration=40, category=beard),
        Service(title="Королевское бритьё", price=1800, duration=60, category=beard),
        Service(title="Камуфляж седины", price=1300, duration=40, category=care),
    ]

    masters = [
        Master(name="Алиса Морозова", services=[services[0], services[1], services[3]]),
        Master(name="Даниил Ковалёв", services=[services[0], services[2], services[4]]),
        Master(name="Екатерина Соколова", services=[services[1], services[5]]),
    ]

    session.add_all([cutting, beard, care, *services, *masters])
    session.flush()

    demo_day = date(2030, 1, 15)
    first_start = datetime.combine(demo_day, time(10, 0))
    second_start = datetime.combine(demo_day, time(12, 0))
    session.add_all(
        [
            Appointment(
                client_name="Иван Петров",
                master=masters[0],
                service=services[0],
                starts_at=first_start,
                ends_at=first_start + timedelta(minutes=services[0].duration),
                status="completed",
            ),
            Appointment(
                client_name="Алексей Смирнов",
                master=masters[1],
                service=services[2],
                starts_at=second_start,
                ends_at=second_start + timedelta(minutes=services[2].duration),
                status="booked",
            ),
        ]
    )
    session.commit()


def get_services_with_categories(session: Session) -> list[tuple[str, str, int, int]]:
    statement = (
        select(Category.title, Service.title, Service.price, Service.duration)
        .join(Category.services)
        .order_by(Category.title, Service.title)
    )
    return list(session.execute(statement).all())


def get_services_by_max_price(session: Session, max_price: int) -> list[Service]:
    statement = (
        select(Service)
        .where(Service.price <= max_price)
        .order_by(Service.price, Service.title)
    )
    return list(session.scalars(statement).all())


def get_masters_for_service(session: Session, service_id: int) -> list[Master]:
    statement = (
        select(Master)
        .join(Master.services)
        .where(Service.id == service_id)
        .order_by(Master.name)
    )
    return list(session.scalars(statement).unique().all())


def get_appointments_for_master(session: Session, master_id: int) -> list[Appointment]:
    statement = (
        select(Appointment)
        .where(Appointment.master_id == master_id)
        .order_by(Appointment.starts_at)
    )
    return list(session.scalars(statement).all())


def get_appointment_counts_by_master(session: Session) -> list[tuple[str, int]]:
    statement = (
        select(Master.name, func.count(Appointment.id))
        .outerjoin(Master.appointments)
        .group_by(Master.id, Master.name)
        .order_by(Master.name)
    )
    return list(session.execute(statement).all())


def get_completed_revenue_by_category(session: Session) -> list[tuple[str, int]]:
    revenue = func.coalesce(
        func.sum(
            case((Appointment.status == "completed", Service.price), else_=0)
        ),
        0,
    )
    statement = (
        select(Category.title, revenue.label("revenue"))
        .outerjoin(Category.services)
        .outerjoin(Service.appointments)
        .group_by(Category.id, Category.title)
        .order_by(Category.title)
    )
    return list(session.execute(statement).all())


def find_conflict(
    session: Session, master_id: int, starts_at: datetime, ends_at: datetime
) -> Appointment | None:
    statement = (
        select(Appointment)
        .where(
            Appointment.master_id == master_id,
            Appointment.status != "cancelled",
            Appointment.starts_at < ends_at,
            starts_at < Appointment.ends_at,
        )
        .order_by(Appointment.starts_at)
        .limit(1)
    )
    return session.scalar(statement)


def free_slots(
    session: Session,
    master_id: int,
    day: date,
    step_minutes: int = 30,
    service_id: int | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(step_minutes, int) or not 15 <= step_minutes <= 120:
        raise ValueError("step_minutes должен быть целым числом от 15 до 120")

    master = session.get(Master, master_id)
    if master is None:
        raise LookupError(f"Мастер с ID {master_id} не найден")

    if service_id is None:
        duration = step_minutes
    else:
        service = session.get(Service, service_id)
        if service is None:
            raise LookupError(f"Услуга с ID {service_id} не найдена")
        if service not in master.services:
            raise ValueError("Мастер не оказывает выбранную услугу")
        duration = service.duration

    day_start, day_end = working_hours(day)
    now = datetime.now()
    slots: list[dict[str, Any]] = []
    current = day_start

    while current + timedelta(minutes=duration) <= day_end:
        candidate_end = current + timedelta(minutes=duration)
        conflict = find_conflict(session, master_id, current, candidate_end)
        is_past = day < now.date() or (day == now.date() and current < now)
        slots.append(
            {"time": current.strftime("%H:%M"), "available": not is_past and conflict is None}
        )
        current += timedelta(minutes=step_minutes)

    return slots


def create_appointment(
    session: Session,
    client_name: str,
    master_id: int,
    service_id: int,
    starts_at: datetime,
) -> Appointment:
    starts_at = normalize_local_datetime(starts_at)
    name = client_name.strip() if isinstance(client_name, str) else ""

    if not 2 <= len(name) <= 80:
        raise ValueError("Имя клиента должно содержать от 2 до 80 символов")

    master = session.get(Master, master_id)
    if master is None:
        raise LookupError(f"Мастер с ID {master_id} не найден")

    service = session.get(Service, service_id)
    if service is None:
        raise LookupError(f"Услуга с ID {service_id} не найдена")

    if service not in master.services:
        raise ValueError("Мастер не оказывает выбранную услугу")

    ends_at = starts_at + timedelta(minutes=service.duration)
    day_start, day_end = working_hours(starts_at.date())

    if starts_at < day_start or ends_at > day_end:
        raise ValueError("Запись должна полностью находиться в рабочем времени с 09:00 до 21:00")
    if starts_at < datetime.now():
        raise ValueError("Нельзя создать запись на время в прошлом")
    if find_conflict(session, master_id, starts_at, ends_at) is not None:
        raise ValueError("Выбранное время занято существующей записью")

    appointment = Appointment(
        client_name=name,
        master_id=master_id,
        service_id=service_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="booked",
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


def cancel_appointment(session: Session, appointment_id: int) -> Appointment:
    appointment = session.get(Appointment, appointment_id)
    if appointment is None:
        raise LookupError(f"Запись с ID {appointment_id} не найдена")
    appointment.status = "cancelled"
    session.commit()
    session.refresh(appointment)
    return appointment


def print_demo_queries(session: Session) -> None:
    print("Услуги и категории:")
    for category, title, price, duration in get_services_with_categories(session):
        print(f"{category}: {title}, {price} руб., {duration} мин.")

    print("\nУслуги стоимостью до 1500 рублей:")
    for service in get_services_by_max_price(session, 1500):
        print(f"{service.title}: {service.price} руб.")

    print("\nКоличество записей по мастерам:")
    for master_name, count in get_appointment_counts_by_master(session):
        print(f"{master_name}: {count}")

    print("\nВыручка по категориям по завершённым записям:")
    for title, total in get_completed_revenue_by_category(session):
        print(f"{title}: {total} руб.")


def create_schema() -> None:
    Base.metadata.create_all(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLAlchemy и Alembic для барбершопа")
    parser.add_argument("command", choices=("init-db", "seed", "queries", "slots"))
    parser.add_argument("--master-id", type=int, default=1)
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--service-id", type=int)
    parser.add_argument("--step-minutes", type=int, default=30)
    args = parser.parse_args()

    if args.command == "init-db":
        create_schema()
        print("Таблицы созданы.")
        return

    with SessionLocal() as session:
        if args.command == "seed":
            seed_data(session)
            print("Демонстрационные данные добавлены или уже существуют.")
        elif args.command == "queries":
            print_demo_queries(session)
        elif args.command == "slots":
            if args.date is None:
                parser.error("Для команды slots укажите --date YYYY-MM-DD")
            for slot in free_slots(
                session,
                args.master_id,
                args.date,
                args.step_minutes,
                args.service_id,
            ):
                state = "свободно" if slot["available"] else "занято"
                print(f"{slot['time']} — {state}")


if __name__ == "__main__":
    main()
