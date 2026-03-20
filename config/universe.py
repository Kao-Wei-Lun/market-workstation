from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


UNIVERSE_DIR = Path(__file__).resolve().parent / "universes"


@dataclass(frozen=True)
class UniverseScopeDefinition:
    key: str
    label: str
    market: str
    asset_type: str
    source_route: str
    coverage: str
    description: str


@dataclass(frozen=True)
class UniverseInstrumentDefinition:
    symbol: str
    name: str
    market: str
    asset_type: str
    currency: str
    timezone: str
    source_route: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class UniverseWatchlistDefinition:
    name: str
    description: str
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True)
class UniversePreset:
    preset_name: str
    description: str
    scopes: tuple[UniverseScopeDefinition, ...] = ()
    instruments: tuple[UniverseInstrumentDefinition, ...] = ()
    watchlists: tuple[UniverseWatchlistDefinition, ...] = ()


def list_available_universe_presets() -> list[str]:
    return sorted(path.stem for path in UNIVERSE_DIR.glob("*.json"))


def load_universe_preset(preset_name: str) -> UniversePreset:
    path = UNIVERSE_DIR / f"{preset_name}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return UniversePreset(
        preset_name=str(payload["preset_name"]),
        description=str(payload["description"]),
        scopes=tuple(_parse_scope(item) for item in _as_object_list(payload.get("scopes", []))),
        instruments=tuple(_parse_instrument(item) for item in _as_object_list(payload.get("instruments", []))),
        watchlists=tuple(_parse_watchlist(item) for item in _as_object_list(payload.get("watchlists", []))),
    )


def _as_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _parse_scope(payload: dict[str, object]) -> UniverseScopeDefinition:
    return UniverseScopeDefinition(
        key=str(payload["key"]),
        label=str(payload["label"]),
        market=str(payload["market"]),
        asset_type=str(payload["asset_type"]),
        source_route=str(payload["source_route"]),
        coverage=str(payload["coverage"]),
        description=str(payload["description"]),
    )


def _parse_instrument(payload: dict[str, object]) -> UniverseInstrumentDefinition:
    return UniverseInstrumentDefinition(
        symbol=str(payload["symbol"]),
        name=str(payload["name"]),
        market=str(payload["market"]),
        asset_type=str(payload["asset_type"]),
        currency=str(payload["currency"]),
        timezone=str(payload["timezone"]),
        source_route=str(payload["source_route"]),
        tags=tuple(_as_string_list(payload.get("tags", []))),
    )


def _parse_watchlist(payload: dict[str, object]) -> UniverseWatchlistDefinition:
    return UniverseWatchlistDefinition(
        name=str(payload["name"]),
        description=str(payload["description"]),
        symbols=tuple(_as_string_list(payload.get("symbols", []))),
    )
