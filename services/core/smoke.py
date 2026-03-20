from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from services.core.bootstrap import SAMPLE_INSTRUMENT_SYMBOLS
from services.models.instrument import Instrument


@dataclass(frozen=True)
class SmokeTestResult:
    database_connectivity_ok: bool
    api_health_ok: bool
    schema_reachable: bool
    sample_data_ok: bool
    checked_symbols: list[str]

    @property
    def passed(self) -> bool:
        return all(
            [
                self.database_connectivity_ok,
                self.api_health_ok,
                self.schema_reachable,
                self.sample_data_ok,
            ]
        )


def run_smoke_test(
    session: Session,
    *,
    api_base_url: str = "http://localhost:8000",
) -> SmokeTestResult:
    database_connectivity_ok = _check_database_connectivity(session)
    schema_reachable = _check_schema_reachable(session)
    api_health_ok = _check_api_health(api_base_url)
    checked_symbols = sorted(SAMPLE_INSTRUMENT_SYMBOLS)
    sample_data_ok = _check_sample_instruments(session, checked_symbols)
    return SmokeTestResult(
        database_connectivity_ok=database_connectivity_ok,
        api_health_ok=api_health_ok,
        schema_reachable=schema_reachable,
        sample_data_ok=sample_data_ok,
        checked_symbols=checked_symbols,
    )


def _check_database_connectivity(session: Session) -> bool:
    return session.execute(text("SELECT 1")).scalar_one() == 1


def _check_schema_reachable(session: Session) -> bool:
    bind = session.get_bind()
    return inspect(bind).has_table("alembic_version")


def _check_api_health(api_base_url: str) -> bool:
    try:
        response = httpx.get(f"{api_base_url.rstrip('/')}/health", timeout=5.0)
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return False
    return response.status_code == 200 and payload.get("status") == "ok"


def _check_sample_instruments(session: Session, expected_symbols: list[str]) -> bool:
    existing_symbols = {
        symbol
        for symbol, in session.query(Instrument.symbol)
        .filter(Instrument.symbol.in_(expected_symbols))
        .all()
    }
    return set(expected_symbols).issubset(existing_symbols)
