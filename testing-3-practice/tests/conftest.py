from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from solution import Base, build_engine


@pytest.fixture
def db_engine(tmp_path: Path):
    engine = build_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False, class_=Session)
    with factory() as session:
        yield session
