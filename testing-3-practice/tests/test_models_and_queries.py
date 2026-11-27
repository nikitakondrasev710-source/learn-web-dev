from datetime import date

from sqlalchemy import func, select

from solution import (
    Appointment,
    Category,
    Master,
    Service,
    get_appointment_counts_by_master,
    get_completed_revenue_by_category,
    get_masters_for_service,
    get_services_with_categories,
    seed_data,
)


def test_seed_data_is_complete_and_idempotent(db_session):
    seed_data(db_session)
    seed_data(db_session)

    assert db_session.scalar(select(func.count(Category.id))) == 3
    assert db_session.scalar(select(func.count(Service.id))) == 6
    assert db_session.scalar(select(func.count(Master.id))) == 3
    assert db_session.scalar(select(func.count(Appointment.id))) == 2


def test_relationships_category_service_and_master_service(db_session):
    seed_data(db_session)
    haircut = db_session.scalar(select(Service).where(Service.title == "Мужская стрижка"))

    assert haircut is not None
    assert haircut.category.title == "Стрижки"
    assert {master.name for master in haircut.masters} == {"Алиса Морозова", "Даниил Ковалёв"}


def test_join_query_returns_services_with_categories(db_session):
    seed_data(db_session)

    rows = get_services_with_categories(db_session)

    assert len(rows) == 6
    assert all(len(row) == 4 for row in rows)


def test_master_lookup_by_service_uses_many_to_many_relationship(db_session):
    seed_data(db_session)
    haircut = db_session.scalar(select(Service).where(Service.title == "Мужская стрижка"))

    masters = get_masters_for_service(db_session, haircut.id)

    assert len(masters) == 2


def test_group_by_count_includes_masters_without_appointments(db_session):
    seed_data(db_session)

    rows = get_appointment_counts_by_master(db_session)

    assert len(rows) == 3
    assert sum(count for _, count in rows) == 2


def test_group_by_sum_returns_completed_revenue(db_session):
    seed_data(db_session)

    rows = dict(get_completed_revenue_by_category(db_session))

    assert rows["Стрижки"] == 1500
    assert rows["Борода и бритьё"] == 0
    assert rows["Уход"] == 0
