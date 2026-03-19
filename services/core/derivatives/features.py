from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import mean, pstdev

from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature


def compute_tw_derivatives_features(
    records: list[TwDerivativesDaily],
) -> list[TwDerivativesFeature]:
    grouped_records: dict[tuple[str, str, str, str | None, str | None], list[TwDerivativesDaily]] = defaultdict(
        list
    )
    for record in records:
        grouped_records[
            (record.market, record.product_code, record.institution, record.contract_period, record.call_put)
        ].append(record)

    features: list[TwDerivativesFeature] = []
    for group_records in grouped_records.values():
        ordered_records = sorted(group_records, key=lambda item: item.trade_date)
        values = [Decimal(record.net_open_interest) for record in ordered_records]

        for index, record in enumerate(ordered_records):
            delta_1d = _compute_delta(values, index, 1)
            delta_5d = _compute_delta(values, index, 5)
            delta_20d = _compute_delta(values, index, 20)
            zscore_20d = _compute_zscore(values, index, 20)
            bias_score = _compute_bias_score(delta_1d, delta_5d, delta_20d, zscore_20d)
            regime_label = _label_regime(bias_score)
            anomaly_flag = zscore_20d is not None and abs(zscore_20d) >= Decimal("2")
            features.append(
                TwDerivativesFeature(
                    daily_record_id=record.id,
                    trade_date=record.trade_date,
                    market=record.market,
                    product_code=record.product_code,
                    contract_period=record.contract_period,
                    institution=record.institution,
                    call_put=record.call_put,
                    delta_1d=delta_1d,
                    delta_5d=delta_5d,
                    delta_20d=delta_20d,
                    zscore_20d=zscore_20d,
                    regime_label=regime_label,
                    bias_score=bias_score,
                    anomaly_flag=anomaly_flag,
                )
            )
    return features


def _compute_delta(values: list[Decimal], index: int, window: int) -> Decimal | None:
    if index < window:
        return None
    return values[index] - values[index - window]


def _compute_zscore(values: list[Decimal], index: int, window: int) -> Decimal | None:
    if index + 1 < window:
        return None
    window_values = values[index + 1 - window : index + 1]
    sample = [float(value) for value in window_values]
    standard_deviation = pstdev(sample)
    if standard_deviation == 0:
        return Decimal("0")
    zscore = (sample[-1] - mean(sample)) / standard_deviation
    return Decimal(f"{zscore:.6f}")


def _compute_bias_score(
    delta_1d: Decimal | None,
    delta_5d: Decimal | None,
    delta_20d: Decimal | None,
    zscore_20d: Decimal | None,
) -> Decimal:
    score = Decimal("0")
    score += _sign_component(delta_1d, Decimal("1"))
    score += _sign_component(delta_5d, Decimal("2"))
    score += _sign_component(delta_20d, Decimal("3"))
    if zscore_20d is not None:
        clipped = max(min(zscore_20d, Decimal("3")), Decimal("-3"))
        score += clipped
    return score


def _sign_component(delta: Decimal | None, weight: Decimal) -> Decimal:
    if delta is None or delta == 0:
        return Decimal("0")
    return weight if delta > 0 else weight * Decimal("-1")


def _label_regime(bias_score: Decimal) -> str:
    if bias_score >= Decimal("3"):
        return "bullish"
    if bias_score <= Decimal("-3"):
        return "bearish"
    return "neutral"
