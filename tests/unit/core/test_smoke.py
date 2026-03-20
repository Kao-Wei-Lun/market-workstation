from __future__ import annotations

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import seed_sample_reference_data
from services.core.smoke import run_smoke_test
from services.db.base import Base
from services.models import import_models


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_smoke_test_checks_database_api_schema_and_seeded_instruments(monkeypatch) -> None:
    session = _build_session()
    seed_sample_reference_data(session)
    monkeypatch.setattr("services.core.smoke.httpx.get", lambda url, timeout: _FakeResponse())

    result = run_smoke_test(session, api_base_url="http://localhost:8000")

    assert result.passed is True
    assert result.database_connectivity_ok is True
    assert result.api_health_ok is True
    assert result.schema_reachable is True
    assert result.sample_data_ok is True
    assert result.checked_symbols == ["2330", "AAPL", "^TWII"]


def test_smoke_test_handles_api_failure(monkeypatch) -> None:
    session = _build_session()
    seed_sample_reference_data(session)

    def raise_http_error(url: str, timeout: float) -> None:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr("services.core.smoke.httpx.get", raise_http_error)

    result = run_smoke_test(session, api_base_url="http://localhost:8000")

    assert result.passed is False
    assert result.api_health_ok is False


class _FakeResponse:
    status_code = 200

    @staticmethod
    def json() -> dict[str, str]:
        return {"status": "ok"}
