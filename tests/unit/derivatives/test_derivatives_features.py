from __future__ import annotations

from datetime import date, timedelta

from services.core.derivatives.features import compute_tw_derivatives_features
from services.models.tw_derivatives_daily import TwDerivativesDaily


def test_feature_computation_builds_expected_metrics() -> None:
    records = [
        TwDerivativesDaily(
            id=index + 1,
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            market="futures",
            product_code="TX",
            institution="foreign_investors",
            long_open_interest=10000 + index * 10,
            short_open_interest=9000,
            net_open_interest=1000 + index * 10,
            source_route="taifex_open_data",
            is_options=False,
        )
        for index in range(25)
    ]

    features = compute_tw_derivatives_features(records)
    latest = features[-1]

    assert len(features) == 25
    assert latest.delta_1d == 10
    assert latest.delta_5d == 50
    assert latest.delta_20d == 200
    assert latest.zscore_20d is not None
    assert latest.regime_label == "bullish"
    assert latest.bias_score > 0
    assert latest.anomaly_flag is False
