from __future__ import annotations

from datetime import date
from decimal import Decimal

from services.core.derivatives.summary import generate_daily_institutional_bias_summary
from services.models.tw_derivatives_feature import TwDerivativesFeature


def test_summary_generation_returns_bias_snapshot() -> None:
    trade_date = date(2024, 1, 2)
    features = [
        TwDerivativesFeature(
            daily_record_id=1,
            trade_date=trade_date,
            market="futures",
            product_code="TX",
            institution="foreign_investors",
            regime_label="bullish",
            bias_score=Decimal("4.5"),
            anomaly_flag=False,
        ),
        TwDerivativesFeature(
            daily_record_id=2,
            trade_date=trade_date,
            market="futures",
            product_code="MTX",
            institution="dealers",
            regime_label="bearish",
            bias_score=Decimal("-2.0"),
            anomaly_flag=True,
        ),
        TwDerivativesFeature(
            daily_record_id=3,
            trade_date=trade_date,
            market="options",
            product_code="TXO",
            institution="investment_trust",
            regime_label="neutral",
            bias_score=Decimal("0.5"),
            anomaly_flag=False,
        ),
    ]

    summary = generate_daily_institutional_bias_summary(trade_date, features)

    assert summary.trade_date == trade_date
    assert summary.bullish_count == 1
    assert summary.bearish_count == 1
    assert summary.neutral_count == 1
    assert summary.anomaly_count == 1
    assert summary.overall_regime == "neutral"
    assert len(summary.highlights) == 3
