from __future__ import annotations

import importlib


def test_low_level_imports_do_not_trigger_circular_imports() -> None:
    connectors_base = importlib.import_module("services.connectors.base")
    schemas_etl = importlib.import_module("services.schemas.etl")
    derivatives_summary = importlib.import_module("services.core.derivatives.summary")
    manage_module = importlib.import_module("scripts.manage")

    assert connectors_base.ConnectorRequest is not None
    assert schemas_etl.NormalizedDataBatch is not None
    assert derivatives_summary.DailyInstitutionalBiasSummary is not None
    assert manage_module.main is not None
