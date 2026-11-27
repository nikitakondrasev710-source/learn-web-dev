from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from solution import (
    Appointment,
    Category,
    Master,
    Service,
    cancel_appointment,
    create_appointment,
    find_conflict,
    free_slots,
    get_appointment_counts_by_master,
    get_completed_revenue_by_category,
    get_masters_for_service,
    get_services_with_categories,
    seed_data,
)


def get_master_and_service(session):
    master = session.scalar(select(Master).where(Master.name == "Алиса Морозова"))
    service = session.scalar(select(Service).where(Service.title == "Мужская стрижка"))
    return master, service


def test_seed_data_is_idempotent(db_session):
    seed_data(db_session)
    seed_data(db_session)
    assert db_session.query(Category).count() == 3
    assert db_session.query(Service).count() == 6
    assert db_session.query(Master).count() == 3
    assert db_session.query(Appointment).count() == 2


def test_relationships_and_many_to_many(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    assert service.category.title == "Стрижки"
    assert master in service.masters
    assert service in master.services


def test_join_query_returns_all_services(db_session):
    seed_data(db_session)
    assert len(get_services_with_categories(db_session)) == 6


def test_masters_for_service(db_session):
    seed_data(db_session)
    _, service = get_master_and_service(db_session)
    assert len(get_masters_for_service(db_session, service.id)) == 2


def test_group_count_includes_all_masters(db_session):
    seed_data(db_session)
    counts = get_appointment_counts_by_master(db_session)
    assert len(counts) == 3
    assert sum(count for _, count in counts) == 2


def test_revenue_counts_only_completed_appointments(db_session):
    seed_data(db_session)
    revenue = dict(get_completed_revenue_by_category(db_session))
    assert revenue["Стрижки"] == 1500
    assert revenue["Борода и бритьё"] == 0
    assert revenue["Уход"] == 0


def test_free_slots_respects_service_duration_and_conflicts(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    target_day = date.today() + timedelta(days=3)
    start = datetime.combine(target_day, time(10, 0))
    db_session.add(
        Appointment(
            client_name="Тестовый клиент",
            master=master,
            service=service,
            starts_at=start,
            ends_at=start + timedelta(minutes=service.duration),
            status="booked",
        )
    )
    db_session.commit()
    slots = free_slots(db_session, master.id, target_day, service_id=service.id)
    availability = {slot["time"]: slot["available"] for slot in slots}
    assert availability["09:00"] is True
    assert availability["09:30"] is False
    assert availability["10:00"] is False
    assert availability["10:30"] is False
    assert availability["11:00"] is True


def test_past_day_has_no_available_slots(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    slots = free_slots(
        db_session, master.id, date.today() - timedelta(days=1), service_id=service.id
    )
    assert slots
    assert all(slot["available"] is False for slot in slots)


def test_free_slots_rejects_unknown_master(db_session):
    seed_data(db_session)
    with pytest.raises(LookupError):
        free_slots(db_session, 9999, date.today() + timedelta(days=1))


def test_free_slots_rejects_invalid_step(db_session):
    seed_data(db_session)
    master, _ = get_master_and_service(db_session)
    with pytest.raises(ValueError):
        free_slots(db_session, master.id, date.today() + timedelta(days=1), step_minutes=0)


def test_create_appointment_and_cancel(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    start = datetime.combine(date.today() + timedelta(days=2), time(10, 0))
    appointment = create_appointment(db_session, "Тестовый клиент", master.id, service.id, start)
    assert appointment.id is not None
    assert appointment.ends_at - appointment.starts_at == timedelta(minutes=service.duration)
    assert cancel_appointment(db_session, appointment.id).status == "cancelled"


def test_create_appointment_rejects_conflict(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    start = datetime.combine(date.today() + timedelta(days=2), time(10, 0))
    create_appointment(db_session, "Первый клиент", master.id, service.id, start)
    with pytest.raises(ValueError, match="занято"):
        create_appointment(
            db_session,
            "Второй клиент",
            master.id,
            service.id,
            start + timedelta(minutes=30),
        )


def test_cancelled_appointment_does_not_block_time(db_session):
    seed_data(db_session)
    master, service = get_master_and_service(db_session)
    start = datetime.combine(date.today() + timedelta(days=2), time(10, 0))
    appointment = create_appointment(db_session, "Клиент", master.id, service.id, start)
    cancel_appointment(db_session, appointment.id)
    assert find_conflict(
        db_session, master.id, start, start + timedelta(minutes=service.duration)
    ) is None


def test_sqlite_foreign_keys_are_enforced(db_session):
    target_day = date.today() + timedelta(days=1)
    invalid = Appointment(
        client_name="Клиент",
        master_id=999999,
        service_id=999999,
        starts_at=datetime.combine(target_day, time(10, 0)),
        ends_at=datetime.combine(target_day, time(11, 0)),
        status="booked",
    )
    db_session.add(invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
