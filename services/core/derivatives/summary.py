from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from services.models.tw_derivatives_feature import TwDerivativesFeature


class DailyInstitutionalBiasSummary(BaseModel):
    trade_date: date
    bullish_count: int
    bearish_count: int
    neutral_count: int
    anomaly_count: int
    average_bias_score: Decimal
    overall_regime: str
    highlights: list[str]


def generate_daily_institutional_bias_summary(
    trade_date: date,
    features: list[TwDerivativesFeature],
) -> DailyInstitutionalBiasSummary:
    if not features:
        return DailyInstitutionalBiasSummary(
            trade_date=trade_date,
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            anomaly_count=0,
            average_bias_score=Decimal("0"),
            overall_regime="neutral",
            highlights=[],
        )

    bullish = [feature for feature in features if feature.regime_label == "bullish"]
    bearish = [feature for feature in features if feature.regime_label == "bearish"]
    neutral = [feature for feature in features if feature.regime_label == "neutral"]
    anomalies = [feature for feature in features if feature.anomaly_flag]
    average_bias_score = sum((feature.bias_score for feature in features), Decimal("0")) / Decimal(
        len(features)
    )
    highlights = [
        (
            f"{feature.institution} {feature.product_code}"
            f"{' ' + feature.call_put if feature.call_put else ''} "
            f"{feature.regime_label} ({feature.bias_score})"
        )
        for feature in sorted(features, key=lambda item: abs(item.bias_score), reverse=True)[:3]
    ]

    return DailyInstitutionalBiasSummary(
        trade_date=trade_date,
        bullish_count=len(bullish),
        bearish_count=len(bearish),
        neutral_count=len(neutral),
        anomaly_count=len(anomalies),
        average_bias_score=average_bias_score.quantize(Decimal("0.000001")),
        overall_regime=_label_overall_regime(average_bias_score),
        highlights=highlights,
    )


def _label_overall_regime(average_bias_score: Decimal) -> str:
    if average_bias_score > Decimal("1"):
        return "bullish"
    if average_bias_score < Decimal("-1"):
        return "bearish"
    return "neutral"
