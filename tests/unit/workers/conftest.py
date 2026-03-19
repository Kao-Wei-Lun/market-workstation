from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.db.base import Base
from services.models import import_models


@pytest.fixture
def worker_session_factory() -> sessionmaker[Session]:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


@pytest.fixture
def worker_session(worker_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = worker_session_factory()
    try:
        yield session
    finally:
        session.close()
