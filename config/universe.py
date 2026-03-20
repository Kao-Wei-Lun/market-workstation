from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


UNIVERSE_DIR = Path(__file__).resolve().parent / "universes"


@dataclass(frozen=True)
class UniverseScopeDefinition:
    key: str
    label: str
    group_label: str
    market: str
    asset_type: str
    source_route: str
    coverage: str
    description: str
    stale_after_days: int = 3


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
    scope_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class UniverseWatchlistDefinition:
    name: str
    description: str
    symbols: tuple[str, ...] = ()
    scope_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class UniversePreset:
    preset_name: str
    description: str
    scopes: tuple[UniverseScopeDefinition, ...] = ()
    instruments: tuple[UniverseInstrumentDefinition, ...] = ()
    watchlists: tuple[UniverseWatchlistDefinition, ...] = ()


def list_available_universe_presets() -> list[str]:
    names = {path.stem for path in UNIVERSE_DIR.glob("*.json")}
    names.update(path.name for path in UNIVERSE_DIR.iterdir() if path.is_dir())
    return sorted(names)


def load_universe_preset(preset_name: str) -> UniversePreset:
    payload = _load_preset_payload(preset_name)
    return UniversePreset(
        preset_name=str(payload["preset_name"]),
        description=str(payload["description"]),
        scopes=tuple(_parse_scope(item) for item in _as_object_list(payload.get("scopes", []))),
        instruments=tuple(_parse_instrument(item) for item in _as_object_list(payload.get("instruments", []))),
        watchlists=tuple(_parse_watchlist(item) for item in _as_object_list(payload.get("watchlists", []))),
    )


def describe_universe_preset(preset_name: str) -> dict[str, object]:
    preset = load_universe_preset(preset_name)
    return {
        "preset_name": preset.preset_name,
        "description": preset.description,
        "scope_keys": [scope.key for scope in preset.scopes],
        "instrument_count": len(preset.instruments),
        "watchlist_count": len(preset.watchlists),
    }


def filter_universe_preset_by_scope(preset: UniversePreset, scope_keys: tuple[str, ...] = ()) -> UniversePreset:
    normalized = tuple(sorted({scope_key.strip() for scope_key in scope_keys if scope_key.strip()}))
    if not normalized:
        return preset

    allowed_scopes = tuple(scope for scope in preset.scopes if scope.key in normalized)
    filtered_instruments = tuple(
        instrument
        for instrument in preset.instruments
        if not instrument.scope_keys or any(scope_key in normalized for scope_key in instrument.scope_keys)
    )
    filtered_symbols = {instrument.symbol for instrument in filtered_instruments}
    filtered_watchlists = tuple(
        UniverseWatchlistDefinition(
            name=watchlist.name,
            description=watchlist.description,
            symbols=tuple(symbol for symbol in watchlist.symbols if symbol in filtered_symbols),
            scope_keys=watchlist.scope_keys,
        )
        for watchlist in preset.watchlists
        if (
            (not watchlist.scope_keys or any(scope_key in normalized for scope_key in watchlist.scope_keys))
            and any(symbol in filtered_symbols for symbol in watchlist.symbols)
        )
    )
    return UniversePreset(
        preset_name=preset.preset_name,
        description=preset.description,
        scopes=allowed_scopes,
        instruments=filtered_instruments,
        watchlists=filtered_watchlists,
    )


def _load_preset_payload(preset_name: str) -> dict[str, object]:
    file_path = UNIVERSE_DIR / f"{preset_name}.json"
    directory_path = UNIVERSE_DIR / preset_name
    if file_path.is_file():
        return _read_json(file_path)
    if directory_path.is_dir():
        return _load_directory_preset(directory_path)
    msg = f"unknown universe preset: {preset_name}"
    raise FileNotFoundError(msg)


def _load_directory_preset(directory_path: Path) -> dict[str, object]:
    manifest_path = directory_path / "manifest.json"
    manifest = _read_json(manifest_path)
    instruments: list[dict[str, object]] = []
    watchlists: list[dict[str, object]] = []
    for segment_name in _as_string_list(manifest.get("segments", [])):
        segment_payload = _read_json(directory_path / f"{segment_name}.json")
        instruments.extend(_as_object_list(segment_payload.get("instruments", [])))
        watchlists.extend(_as_object_list(segment_payload.get("watchlists", [])))
    return {
        "preset_name": manifest["preset_name"],
        "description": manifest["description"],
        "scopes": manifest.get("scopes", []),
        "instruments": instruments,
        "watchlists": watchlists,
    }


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"universe payload must be a JSON object: {path}"
        raise ValueError(msg)
    return payload


def _as_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _parse_scope(payload: dict[str, object]) -> UniverseScopeDefinition:
    return UniverseScopeDefinition(
        key=str(payload["key"]),
        label=str(payload["label"]),
        group_label=str(payload.get("group_label", payload["market"])),
        market=str(payload["market"]),
        asset_type=str(payload["asset_type"]),
        source_route=str(payload["source_route"]),
        coverage=str(payload["coverage"]),
        description=str(payload["description"]),
        stale_after_days=_as_int(payload.get("stale_after_days"), 3),
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
        scope_keys=tuple(_as_string_list(payload.get("scope_keys", []))),
    )


def _parse_watchlist(payload: dict[str, object]) -> UniverseWatchlistDefinition:
    return UniverseWatchlistDefinition(
        name=str(payload["name"]),
        description=str(payload["description"]),
        symbols=tuple(_as_string_list(payload.get("symbols", []))),
        scope_keys=tuple(_as_string_list(payload.get("scope_keys", []))),
    )
