from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_downgrade_upgrade_on_clean_database(tmp_path, monkeypatch):
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    config = Config(str(PROJECT_DIR / "alembic.ini"))
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {"categories", "services", "masters", "master_services", "appointments", "alembic_version"}.issubset(tables)
    finally:
        engine.dispose()

    command.downgrade(config, "base")

    engine = create_engine(database_url)
    try:
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert {"categories", "services", "masters", "master_services", "appointments"}.issubset(tables)
    finally:
        engine.dispose()
