"""Создание начальной схемы базы данных салона."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
        sqlite_autoincrement=True,
    )

    op.create_table(
        "masters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.CheckConstraint("price >= 0", name="ck_services_price_nonnegative"),
        sa.CheckConstraint("duration > 0", name="ck_services_duration_positive"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
    )
    op.create_index("ix_services_category_id", "services", ["category_id"])

    op.create_table(
        "master_services",
        sa.Column("master_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("master_id", "service_id"),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_name", sa.String(length=80), nullable=False),
        sa.Column("master_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_appointments_end_after_start"),
        sa.CheckConstraint(
            "status IN ('booked', 'completed', 'cancelled')",
            name="ck_appointments_status_valid",
        ),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appointments_master_starts_at",
        "appointments",
        ["master_id", "starts_at"],
    )
    op.create_index("ix_appointments_service_id", "appointments", ["service_id"])


def downgrade() -> None:
    op.drop_index("ix_appointments_service_id", table_name="appointments")
    op.drop_index("ix_appointments_master_starts_at", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("master_services")
    op.drop_index("ix_services_category_id", table_name="services")
    op.drop_table("services")
    op.drop_table("masters")
    op.drop_table("categories")
