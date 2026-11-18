"""
[Backend] Задание 3 — SQLAlchemy и Alembic.

Модели базы данных для салона: категории, услуги, мастера и записи.
Показаны связи (один-ко-многим, многие-ко-многим), запросы через ORM,
бизнес-логика свободных слотов и миграции.

Запуск:
    pip install sqlalchemy alembic
    python solution.py          # создаёт salon.db и наполняет данными
    alembic upgrade head        # применяет миграции (см. alembic/)
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)


# ---------------------------------------------------------------
# 1. Базовый класс и ассоциативная таблица
# ---------------------------------------------------------------

class Base(DeclarativeBase):
    """Базовый класс моделей."""


# Связь «многие-ко-многим»: мастер умеет делать несколько услуг,
# одну услугу делают несколько мастеров.
master_services = Table(
    "master_services",
    Base.metadata,
    Column("master_id", ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


# ---------------------------------------------------------------
# 2. Модели
# ---------------------------------------------------------------

class Category(Base):
    """Категория услуг: стрижки, ногтевой сервис, барбер."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    services: Mapped[list["Service"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category {self.title}>"


class Service(Base):
    """Услуга салона."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    price: Mapped[int] = mapped_column(Integer)
    duration: Mapped[int] = mapped_column(Integer, comment="Длительность, минуты")
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship(back_populates="services")
    masters: Mapped[list["Master"]] = relationship(
        secondary=master_services,
        back_populates="services",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="service"
    )

    def __repr__(self) -> str:
        return f"<Service {self.title} {self.price}₽ {self.duration}мин>"


class Master(Base):
    """Мастер салона."""

    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    specialization: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    services: Mapped[list["Service"]] = relationship(
        secondary=master_services,
        back_populates="masters",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="master",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Master {self.name}>"


class Appointment(Base):
    """Запись клиента."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String(120), index=True)
    client_phone: Mapped[str] = mapped_column(String(30), default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="new")
    comment: Mapped[str] = mapped_column(String(300), default="")

    master_id: Mapped[int] = mapped_column(
        ForeignKey("masters.id", ondelete="CASCADE"), index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )

    master: Mapped["Master"] = relationship(back_populates="appointments")
    service: Mapped["Service"] = relationship(back_populates="appointments")

    def __repr__(self) -> str:
        return (
            f"<Appointment {self.starts_at:%d.%m %H:%M} "
            f"{self.client_name} — {self.service.title}>"
        )


# ---------------------------------------------------------------
# 3. Подключение к базе
# ---------------------------------------------------------------

engine = create_engine("sqlite:///salon.db", echo=False)

# В реальном проекте схему создают миграции Alembic,
# здесь — для наглядности и запуска без Alembic.
Base.metadata.create_all(engine)


# ---------------------------------------------------------------
# 4. Наполнение данными
# ---------------------------------------------------------------

def seed(session: Session) -> None:
    """Заполняет базу тестовыми данными, если она пуста."""
    if session.scalar(select(func.count()).select_from(Category)):
        return

    haircuts = Category(title="Стрижки", slug="haircuts")
    nails = Category(title="Ногтевой сервис", slug="nails")
    barber = Category(title="Барбер", slug="barber")

    session.add_all([haircuts, nails, barber])
    session.flush()

    services = [
        Service(title="Стрижка женская", price=2500, duration=90, category_id=haircuts.id),
        Service(title="Стрижка мужская", price=1500, duration=60, category_id=haircuts.id),
        Service(title="Маникюр", price=2000, duration=90, category_id=nails.id),
        Service(title="Педикюр", price=2800, duration=120, category_id=nails.id),
        Service(title="Бритьё опасной бритвой", price=1200, duration=40, category_id=barber.id),
        Service(title="Оформление бороды", price=800, duration=30, category_id=barber.id),
    ]
    session.add_all(services)
    session.flush()

    alisa = Master(name="Алиса Морозова", specialization="парикмахер-стилист")
    daniil = Master(name="Даниил Ковалёв", specialization="барбер")
    ekaterina = Master(name="Екатерина Соколова", specialization="мастер ногтевого сервиса")

    alisa.services = [services[0], services[1], services[4]]
    daniil.services = [services[1], services[4], services[5]]
    ekaterina.services = [services[2], services[3]]

    session.add_all([alisa, daniil, ekaterina])
    session.flush()

    tomorrow = date.today() + timedelta(days=1)

    session.add_all([
        Appointment(
            client_name="Никита",
            client_phone="+7 900 000-00-01",
            master_id=alisa.id,
            service_id=services[1].id,
            starts_at=datetime.combine(tomorrow, time(10, 0)),
            ends_at=datetime.combine(tomorrow, time(11, 0)),
            status="confirmed",
        ),
        Appointment(
            client_name="Олег",
            client_phone="+7 900 000-00-02",
            master_id=daniil.id,
            service_id=services[5].id,
            starts_at=datetime.combine(tomorrow, time(12, 0)),
            ends_at=datetime.combine(tomorrow, time(12, 30)),
        ),
    ])

    session.commit()


# ---------------------------------------------------------------
# 5. Запросы через ORM
# ---------------------------------------------------------------

def demo_queries(session: Session) -> None:
    print("=== Категории и число услуг в каждой ===")
    statement = (
        select(Category.title, func.count(Service.id))
        .join(Service)
        .group_by(Category.id)
        .order_by(func.count(Service.id).desc())
    )
    for title, count in session.execute(statement):
        print(f"  {title}: {count}")

    print("\n=== Дорогие услуги (> 1500 ₽) ===")
    expensive = session.scalars(
        select(Service).where(Service.price > 1500).order_by(Service.price.desc())
    ).all()
    for service in expensive:
        print(f"  {service.title} — {service.price} ₽")

    print("\n=== Мастера и их услуги ===")
    for master in session.scalars(select(Master).order_by(Master.id)):
        titles = ", ".join(s.title for s in master.services)
        print(f"  {master.name} ({master.specialization}): {titles}")

    print("\n=== Кто делает мужскую стрижку ===")
    male_cut = session.scalar(
        select(Service).where(Service.title == "Стрижка мужская")
    )
    for master in male_cut.masters:
        print(f"  {master.name}")

    print("\n=== Записи на завтра с именами мастера и услуги ===")
    tomorrow = date.today() + timedelta(days=1)
    start = datetime.combine(tomorrow, time.min)
    end = datetime.combine(tomorrow, time.max)

    statement = (
        select(Appointment, Master.name, Service.title)
        .join(Master, Appointment.master_id == Master.id)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.starts_at.between(start, end))
        .order_by(Appointment.starts_at)
    )
    for appointment, master_name, service_title in session.execute(statement):
        print(
            f"  {appointment.starts_at:%H:%M} — {appointment.client_name} "
            f"к {master_name}: {service_title}"
        )

    print("\n=== Выручка по категориям ===")
    statement = (
        select(Category.title, func.sum(Service.price))
        .join(Service, Service.id == Category.id)
        .group_by(Category.id)
    )
    # Для реальной выручки нужен join через записи:
    statement = (
        select(Category.title, func.sum(Service.price))
        .join(Service, Service.category_id == Category.id)
        .join(Appointment, Appointment.service_id == Service.id)
        .group_by(Category.id)
    )
    for title, total in session.execute(statement):
        print(f"  {title}: {total} ₽")


# ---------------------------------------------------------------
# 6. Бизнес-логика: свободные слоты мастера
# ---------------------------------------------------------------

def free_slots(
    session: Session,
    master_id: int,
    day: date,
    step_minutes: int = 30,
    open_hour: int = 9,
    close_hour: int = 21,
) -> list[str]:
    """Свободные слоты мастера на день — на основе данных из БД."""
    busy = session.scalars(
        select(Appointment).where(
            Appointment.master_id == master_id,
            Appointment.starts_at >= datetime.combine(day, time.min),
            Appointment.starts_at <= datetime.combine(day, time.max),
            Appointment.status != "cancelled",
        )
    ).all()

    result: list[str] = []
    current = datetime.combine(day, time(open_hour, 0))
    end = datetime.combine(day, time(close_hour, 0))

    while current < end:
        candidate_end = current + timedelta(minutes=step_minutes)
        busy_now = any(
            a.starts_at < candidate_end and current < a.ends_at for a in busy
        )
        if not busy_now:
            result.append(f"{current:%H:%M}")
        current = candidate_end

    return result


def demo_slots(session: Session) -> None:
    tomorrow = date.today() + timedelta(days=1)

    print(f"\n=== Свободные слоты на {tomorrow:%d.%m.%Y} ===")
    for master in session.scalars(select(Master).order_by(Master.id)):
        slots = free_slots(session, master.id, tomorrow)
        occupied = "занято в " + ", ".join(
            f"{a.starts_at:%H:%M}"
            for a in master.appointments
            if a.starts_at.date() == tomorrow
        ) if master.appointments else "всё свободно"
        print(f"\n  {master.name} — {occupied}")
        print(f"    {', '.join(slots)}")


# ---------------------------------------------------------------
# 7. Точка входа
# ---------------------------------------------------------------

def main() -> None:
    with Session(engine) as session:
        seed(session)
        demo_queries(session)
        demo_slots(session)

    print("\n=== Итог ===")
    with Session(engine) as session:
        print(f"Категорий: {session.scalar(select(func.count()).select_from(Category))}")
        print(f"Услуг: {session.scalar(select(func.count()).select_from(Service))}")
        print(f"Мастеров: {session.scalar(select(func.count()).select_from(Master))}")
        print(f"Записей: {session.scalar(select(func.count()).select_from(Appointment))}")


if __name__ == "__main__":
    main()
