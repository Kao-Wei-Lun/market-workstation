from config.universe import (
    describe_universe_preset,
    filter_universe_preset_by_scope,
    list_available_universe_presets,
    load_universe_preset,
)


def test_list_available_universe_presets_includes_directory_and_json_presets() -> None:
    presets = list_available_universe_presets()

    assert "sample_reference" in presets
    assert "v1_market_expanded" in presets


def test_load_directory_backed_universe_preset_combines_segments() -> None:
    preset = load_universe_preset("v1_market_expanded")

    assert preset.preset_name == "v1_market_expanded"
    assert len(preset.scopes) >= 5
    assert all(scope.group_label for scope in preset.scopes)
    assert all(scope.stale_after_days > 0 for scope in preset.scopes)
    assert any(item.asset_type == "commodity" for item in preset.instruments)
    assert any(item.asset_type == "macro" for item in preset.instruments)
    assert any(watchlist.name == "us-core" for watchlist in preset.watchlists)


def test_filter_universe_preset_by_scope_limits_instruments_and_watchlists() -> None:
    preset = load_universe_preset("v1_market_expanded")
    filtered = filter_universe_preset_by_scope(preset, ("macro_series_core",))

    assert {scope.key for scope in filtered.scopes} == {"macro_series_core"}
    assert filtered.instruments
    assert all("macro_series_core" in instrument.scope_keys for instrument in filtered.instruments)
    assert filtered.watchlists
    assert all("macro_series_core" in watchlist.scope_keys for watchlist in filtered.watchlists)


def test_describe_universe_preset_returns_summary_counts() -> None:
    description = describe_universe_preset("sample_reference")

    assert description["preset_name"] == "sample_reference"
    assert description["instrument_count"] == 3
    assert description["watchlist_count"] == 1
