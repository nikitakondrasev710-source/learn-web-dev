"""Создание начальной схемы базы данных салона.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-19

Миграция создаёт таблицы categories, services, masters,
master_services и appointments — ровно то, что описано в моделях.

Применение:
    alembic upgrade head

Откат:
    alembic downgrade base
"""

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Категории услуг.
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_categories_title", "categories", ["title"], unique=True)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    # Услуги.
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_services_title", "services", ["title"])
    op.create_index("ix_services_category_id", "services", ["category_id"])

    # Мастера.
    op.create_table(
        "masters",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "specialization", sa.String(length=120), nullable=False, server_default=""
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_masters_name", "masters", ["name"])

    # Связь «мастер умеет делать услугу».
    op.create_table(
        "master_services",
        sa.Column("master_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["master_id"], ["masters.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("master_id", "service_id"),
    )

    # Записи клиентов.
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("client_name", sa.String(length=120), nullable=False),
        sa.Column(
            "client_phone", sa.String(length=30), nullable=False, server_default=""
        ),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("comment", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("master_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["master_id"], ["masters.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_appointments_client_name", "appointments", ["client_name"])
    op.create_index("ix_appointments_starts_at", "appointments", ["starts_at"])
    op.create_index("ix_appointments_master_id", "appointments", ["master_id"])
    op.create_index("ix_appointments_service_id", "appointments", ["service_id"])


def downgrade() -> None:
    op.drop_table("appointments")
    op.drop_table("master_services")
    op.drop_table("masters")
    op.drop_table("services")
    op.drop_table("categories")
