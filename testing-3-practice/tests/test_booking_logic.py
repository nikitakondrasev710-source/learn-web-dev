from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select

from solution import (
    Appointment,
    Master,
    Service,
    cancel_appointment,
    create_appointment,
    find_conflict,
    free_slots,
    seed_data,
)


def get_master_and_service(db_session):
    master = db_session.scalar(select(Master).where(Master.name == "Алиса Морозова"))
    service = db_session.scalar(select(Service).where(Service.title == "Мужская стрижка"))
    return master, service


def test_free_slots_accounts_for_service_duration_and_conflicts(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    target_day = date.today() + timedelta(days=3)
    start = datetime.combine(target_day, time(10, 0))
    db_session.add(
        Appointment(
            client_name="Тестовый клиент",
            master_id=master.id,
            service_id=service.id,
            starts_at=start,
            ends_at=start + timedelta(minutes=service.duration),
            status="booked",
        )
    )
    db_session.commit()

    slots = free_slots(
        db_session,
        master_id=master.id,
        day=target_day,
        step_minutes=30,
        service_id=service.id,
    )
    availability = {slot["time"]: slot["available"] for slot in slots}

    assert availability["09:00"] is True
    assert availability["09:30"] is False
    assert availability["10:00"] is False
    assert availability["10:30"] is False
    assert availability["11:00"] is True
    assert slots[-1]["time"] == "20:00"


def test_free_slots_does_not_return_slots_for_past_days(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)

    slots = free_slots(
        db_session,
        master_id=master.id,
        day=date.today() - timedelta(days=1),
        service_id=service.id,
    )

    assert slots
    assert all(slot["available"] is False for slot in slots)


def test_free_slots_rejects_unknown_master(db_session):
    seed_data(db_session)

    with pytest.raises(LookupError, match="не найден"):
        free_slots(db_session, master_id=9999, day=date.today() + timedelta(days=1))


def test_free_slots_rejects_service_not_provided_by_master(db_session):
    seed_data(db_session)
    master = db_session.scalar(select(Master).where(Master.name == "Алиса Морозова"))
    other_service = db_session.scalar(select(Service).where(Service.title == "Стрижка бороды"))

    with pytest.raises(ValueError, match="не оказывает"):
        free_slots(
            db_session,
            master_id=master.id,
            day=date.today() + timedelta(days=1),
            service_id=other_service.id,
        )


def test_free_slots_rejects_invalid_step(db_session):
    seed_data(db_session)
    master, _ = get_master_and_service(db_session)

    with pytest.raises(ValueError, match="step_minutes"):
        free_slots(db_session, master.id, date.today() + timedelta(days=1), step_minutes=0)


def test_create_appointment_success_and_timezone_normalization(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    future_day = date.today() + timedelta(days=2)
    aware_start = datetime.combine(future_day, time(10, 0), tzinfo=timezone.utc)

    appointment = create_appointment(
        db_session,
        client_name="Тестовый клиент",
        master_id=master.id,
        service_id=service.id,
        starts_at=aware_start,
    )

    assert appointment.id is not None
    assert appointment.ends_at - appointment.starts_at == timedelta(minutes=service.duration)
    assert appointment.status == "booked"
    assert appointment.starts_at.tzinfo is None


def test_create_appointment_rejects_overlapping_booking(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    future_day = date.today() + timedelta(days=2)
    first_start = datetime.combine(future_day, time(10, 0))
    create_appointment(db_session, "Первый клиент", master.id, service.id, first_start)

    with pytest.raises(ValueError, match="Время занято"):
        create_appointment(
            db_session,
            "Второй клиент",
            master.id,
            service.id,
            first_start + timedelta(minutes=30),
        )


def test_cancelled_appointment_does_not_block_time(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    future_day = date.today() + timedelta(days=2)
    start = datetime.combine(future_day, time(10, 0))
    appointment = create_appointment(db_session, "Клиент", master.id, service.id, start)

    cancel_appointment(db_session, appointment.id)

    assert find_conflict(
        db_session,
        master.id,
        start,
        start + timedelta(minutes=service.duration),
    ) is None


def test_sqlite_foreign_keys_are_enabled(db_session):
    from sqlalchemy.exc import IntegrityError

    invalid = Appointment(
        client_name="Клиент",
        master_id=999999,
        service_id=999999,
        starts_at=datetime.combine(date.today() + timedelta(days=1), time(10, 0)),
        ends_at=datetime.combine(date.today() + timedelta(days=1), time(11, 0)),
        status="booked",
    )
    db_session.add(invalid)

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
