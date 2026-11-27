from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from solution import Base, build_engine


@pytest.fixture
def db_engine(tmp_path: Path):
    database_path = tmp_path / "test.db"
    test_engine = build_engine(f"sqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    factory = sessionmaker(
        bind=db_engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )
    with factory() as session:
        yield session
