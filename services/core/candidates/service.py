from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import json
from typing import Any

from sqlalchemy.orm import Session

from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.core.derivatives.summary import generate_daily_institutional_bias_summary
from services.core.exports import rows_to_csv
from services.db.repositories.candidates import CandidateItemRepository, CandidateRunRepository
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem

SMA20_SIGNATURE = "period=20"
RSI14_SIGNATURE = "period=14"
MACD_SIGNATURE = "fast_period=12,slow_period=26,signal_period=9"


@dataclass(frozen=True)
class RankedCandidate:
    instrument_id: int
    symbol: str
    candidate_date: date
    score: Decimal
    rank: int
    candidate_reasons: list[str]
    supporting_metrics: dict[str, Any]


@dataclass(frozen=True)
class CandidateGenerationResult:
    candidate_date: date
    generation_config: dict[str, Any]
    summary: dict[str, Any]
    items: list[RankedCandidate]


def build_candidate_generation(
    session: Session,
    *,
    candidate_date: date,
    top_n: int = 20,
) -> CandidateGenerationResult:
    rows = (
        session.query(DailyBar, Instrument)
        .join(Instrument, Instrument.id == DailyBar.instrument_id)
        .filter(DailyBar.trade_date == candidate_date, Instrument.is_active.is_(True))
        .order_by(Instrument.symbol.asc())
        .all()
    )
    instrument_ids = [bar.instrument_id for bar, _instrument in rows]
    indicators = _load_indicator_maps(session, instrument_ids=instrument_ids, candidate_date=candidate_date)
    tag_map = _load_tag_map(session, instrument_ids=instrument_ids)
    watchlist_map = _load_watchlist_map(session, instrument_ids=instrument_ids)
    scanner_context = _build_scanner_context(session, candidate_date=candidate_date)
    derivatives_context = _build_derivatives_context(session, candidate_date=candidate_date)

    unranked: list[tuple[Instrument, DailyBar, Decimal, list[str], dict[str, Any]]] = []
    for bar, instrument in rows:
        score, reasons, metrics = _score_instrument(
            instrument=instrument,
            bar=bar,
            indicators=indicators,
            tag_names=tag_map.get(instrument.id, []),
            watchlists=watchlist_map.get(instrument.id, []),
            scanner_context=scanner_context,
            derivatives_context=derivatives_context,
        )
        if score < Decimal("2.000000") or len(reasons) < 2:
            continue
        unranked.append((instrument, bar, score, reasons, metrics))

    unranked.sort(
        key=lambda item: (
            item[2],
            _safe_decimal(item[4].get("change_percent")),
            item[1].volume,
            item[0].symbol,
        ),
        reverse=True,
    )

    items: list[RankedCandidate] = []
    for index, (instrument, _bar, score, reasons, metrics) in enumerate(unranked[:top_n], start=1):
        items.append(
            RankedCandidate(
                instrument_id=instrument.id,
                symbol=instrument.symbol,
                candidate_date=candidate_date,
                score=score,
                rank=index,
                candidate_reasons=reasons,
                supporting_metrics=metrics,
            )
        )

    summary = {
        "overall_derivatives_regime": derivatives_context["overall_regime"],
        "overall_derivatives_bias_score": str(derivatives_context["average_bias_score"]),
        "instruments_considered": len(rows),
        "eligible_candidates": len(items),
    }
    generation_config = {"top_n": top_n}
    return CandidateGenerationResult(
        candidate_date=candidate_date,
        generation_config=generation_config,
        summary=summary,
        items=items,
    )


def generate_and_persist_candidate_run(
    session: Session,
    *,
    candidate_date: date,
    top_n: int = 20,
) -> tuple[CandidateRun, list[CandidateItem]]:
    generation = build_candidate_generation(session, candidate_date=candidate_date, top_n=top_n)
    run_repository = CandidateRunRepository(session)
    item_repository = CandidateItemRepository(session)
    run = run_repository.create(
        candidate_date=generation.candidate_date,
        status="completed",
        total_candidates=len(generation.items),
        generation_config_json=generation.generation_config,
        summary_json=generation.summary,
    )
    items = [
        CandidateItem(
            run_id=run.id,
            instrument_id=item.instrument_id,
            candidate_date=item.candidate_date,
            symbol=item.symbol,
            score=item.score,
            rank=item.rank,
            candidate_reasons_json=item.candidate_reasons,
            supporting_metrics_json=item.supporting_metrics,
        )
        for item in generation.items
    ]
    item_repository.create_many(items)
    session.commit()
    session.refresh(run)
    persisted_items = item_repository.list_for_run(run.id)
    return run, persisted_items


def get_candidate_run(session: Session, run_id: int) -> CandidateRun | None:
    return CandidateRunRepository(session).get(run_id)


def get_latest_candidate_run_for_date(session: Session, candidate_date: date) -> CandidateRun | None:
    return CandidateRunRepository(session).get_latest_by_date(candidate_date)


def get_latest_candidate_run(session: Session) -> CandidateRun | None:
    return CandidateRunRepository(session).get_latest_run()


def list_candidate_runs(
    session: Session,
    *,
    candidate_date: date | None = None,
    limit: int | None = None,
) -> list[CandidateRun]:
    return CandidateRunRepository(session).list_runs(candidate_date=candidate_date, limit=limit)


def list_candidate_items(
    session: Session,
    run_id: int | None = None,
    *,
    candidate_date: date | None = None,
    symbol: str | None = None,
) -> list[CandidateItem]:
    if run_id is not None and candidate_date is None and symbol is None:
        return CandidateItemRepository(session).list_for_run(run_id)
    return CandidateItemRepository(session).list_items(run_id=run_id, candidate_date=candidate_date, symbol=symbol)


def export_candidate_items(
    session: Session,
    *,
    run_id: int,
    export_format: str,
) -> tuple[str, str]:
    items = list_candidate_items(session, run_id)
    if export_format == "json":
        return (
            f"candidate_run_{run_id}.json",
            json.dumps(
                [
                    {
                        "run_id": item.run_id,
                        "candidate_date": item.candidate_date.isoformat(),
                        "symbol": item.symbol,
                        "score": str(item.score),
                        "rank": item.rank,
                        "candidate_reasons": item.candidate_reasons_json,
                        "supporting_metrics": item.supporting_metrics_json,
                    }
                    for item in items
                ],
                indent=2,
            ),
        )
    rows = [
        {
            "run_id": item.run_id,
            "candidate_date": item.candidate_date.isoformat(),
            "symbol": item.symbol,
            "score": str(item.score),
            "rank": item.rank,
            "candidate_reasons": item.candidate_reasons_json,
            "supporting_metrics": item.supporting_metrics_json,
        }
        for item in items
    ]
    return f"candidate_run_{run_id}.csv", rows_to_csv(rows)


def _score_instrument(
    *,
    instrument: Instrument,
    bar: DailyBar,
    indicators: dict[str, dict[int, Decimal]],
    tag_names: list[str],
    watchlists: list[dict[str, Any]],
    scanner_context: dict[str, dict[str, Any]],
    derivatives_context: dict[str, Any],
) -> tuple[Decimal, list[str], dict[str, Any]]:
    reasons: list[str] = []
    technical_score = Decimal("0")
    momentum_score = Decimal("0")
    group_strength_score = Decimal("0")
    watchlist_bonus = Decimal("0")
    derivatives_bonus = Decimal("0")

    sma20 = indicators["sma20"].get(instrument.id)
    rsi14 = indicators["rsi14"].get(instrument.id)
    macd_histogram = indicators["macd_histogram"].get(instrument.id)
    change_percent = _resolve_close_change_pct(bar)

    if sma20 is not None and bar.close > sma20:
        technical_score += Decimal("2")
        reasons.append("close_above_sma20")
    if rsi14 is not None and Decimal("50") <= rsi14 <= Decimal("70"):
        technical_score += Decimal("1")
        reasons.append("rsi14_bullish_range")
    if macd_histogram is not None and macd_histogram > 0:
        technical_score += Decimal("1")
        reasons.append("macd_histogram_positive")

    if change_percent >= Decimal("2"):
        momentum_score += Decimal("2")
        reasons.append("strong_positive_close_change")
    elif change_percent > 0:
        momentum_score += Decimal("1")
        reasons.append("positive_close_change")

    volume_ratio = _safe_decimal(None)
    scanner_hits = 0
    scanner_memberships = _scanner_memberships_for_instrument(
        instrument_id=instrument.id,
        tag_names=tag_names,
        watchlists=watchlists,
        scanner_context=scanner_context,
    )
    for membership in scanner_memberships:
        group_strength_score += _safe_decimal(membership.get("group_strength_contribution"))
        if membership.get("flagged"):
            scanner_hits += 1
    if scanner_hits > 0:
        reasons.append("group_scanner_flagged")
    if scanner_memberships:
        average_volume_ratio = sum(
            (_safe_decimal(item.get("average_volume_ratio")) for item in scanner_memberships),
            Decimal("0"),
        ) / Decimal(len(scanner_memberships))
        volume_ratio = average_volume_ratio.quantize(Decimal("0.000001"))

    if watchlists:
        watchlist_bonus += Decimal("0.750000")
        reasons.append("watchlist_member")

    if instrument.market == "TW":
        if derivatives_context["overall_regime"] == "bullish":
            derivatives_bonus += Decimal("0.750000")
            reasons.append("bullish_derivatives_context")
        elif derivatives_context["overall_regime"] == "bearish":
            derivatives_bonus -= Decimal("0.750000")
            reasons.append("bearish_derivatives_context")

    total_score = (
        technical_score + momentum_score + group_strength_score + watchlist_bonus + derivatives_bonus
    ).quantize(Decimal("0.000001"))
    metrics = {
        "close": str(bar.close),
        "change_percent": str(change_percent),
        "sma20": str(sma20) if sma20 is not None else None,
        "rsi14": str(rsi14) if rsi14 is not None else None,
        "macd_histogram": str(macd_histogram) if macd_histogram is not None else None,
        "technical_score": str(technical_score.quantize(Decimal("0.000001"))),
        "momentum_score": str(momentum_score.quantize(Decimal("0.000001"))),
        "group_strength_score": str(group_strength_score.quantize(Decimal("0.000001"))),
        "watchlist_bonus": str(watchlist_bonus.quantize(Decimal("0.000001"))),
        "derivatives_context_bonus": str(derivatives_bonus.quantize(Decimal("0.000001"))),
        "watchlists": [item["name"] for item in watchlists],
        "tags": sorted(tag_names),
        "scanner_memberships": scanner_memberships,
        "average_group_volume_ratio": str(volume_ratio) if volume_ratio is not None else None,
        "derivatives_regime": derivatives_context["overall_regime"],
    }
    return total_score, _dedupe_preserve_order(reasons), metrics


def _load_indicator_maps(
    session: Session,
    *,
    instrument_ids: list[int],
    candidate_date: date,
) -> dict[str, dict[int, Decimal]]:
    rows = (
        session.query(IndicatorValue)
        .filter(
            IndicatorValue.instrument_id.in_(instrument_ids),
            IndicatorValue.trade_date == candidate_date,
        )
        .all()
    )
    maps: dict[str, dict[int, Decimal]] = {
        "sma20": {},
        "rsi14": {},
        "macd_histogram": {},
    }
    for row in rows:
        if row.indicator_name == "sma" and row.component == "value" and row.parameter_signature == SMA20_SIGNATURE:
            maps["sma20"][row.instrument_id] = row.value
        elif row.indicator_name == "rsi" and row.component == "value" and row.parameter_signature == RSI14_SIGNATURE:
            maps["rsi14"][row.instrument_id] = row.value
        elif (
            row.indicator_name == "macd"
            and row.component == "histogram"
            and row.parameter_signature == MACD_SIGNATURE
        ):
            maps["macd_histogram"][row.instrument_id] = row.value
    return maps


def _load_tag_map(session: Session, *, instrument_ids: list[int]) -> dict[int, list[str]]:
    tag_map: dict[int, list[str]] = {instrument_id: [] for instrument_id in instrument_ids}
    rows = (
        session.query(InstrumentTag.instrument_id, InstrumentTag.tag)
        .filter(InstrumentTag.instrument_id.in_(instrument_ids))
        .order_by(InstrumentTag.instrument_id.asc(), InstrumentTag.tag.asc())
        .all()
    )
    for instrument_id, tag in rows:
        tag_map.setdefault(instrument_id, []).append(tag)
    return tag_map


def _load_watchlist_map(session: Session, *, instrument_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    watchlist_map: dict[int, list[dict[str, Any]]] = {instrument_id: [] for instrument_id in instrument_ids}
    rows = (
        session.query(WatchlistItem.instrument_id, Watchlist.id, Watchlist.name)
        .join(Watchlist, Watchlist.id == WatchlistItem.watchlist_id)
        .filter(WatchlistItem.instrument_id.in_(instrument_ids))
        .order_by(WatchlistItem.instrument_id.asc(), Watchlist.id.asc())
        .all()
    )
    for instrument_id, watchlist_id, watchlist_name in rows:
        watchlist_map.setdefault(instrument_id, []).append({"id": watchlist_id, "name": watchlist_name})
    return watchlist_map


def _build_scanner_context(session: Session, *, candidate_date: date) -> dict[str, dict[str, Any]]:
    context: dict[str, dict[str, Any]] = {}
    tags = [tag for (tag,) in session.query(InstrumentTag.tag).distinct().order_by(InstrumentTag.tag.asc()).all()]
    for tag in tags:
        scan = scan_tag_group(session, tag=tag, trade_date=candidate_date)
        context[f"tag:{tag}"] = _scanner_summary_dict(scan)

    watchlists = session.query(Watchlist).order_by(Watchlist.id.asc()).all()
    for watchlist in watchlists:
        scan = scan_watchlist_group(session, watchlist_id=watchlist.id, trade_date=candidate_date)
        context[f"watchlist:{watchlist.id}"] = _scanner_summary_dict(scan, watchlist_name=watchlist.name)
    return context


def _scanner_summary_dict(scan, watchlist_name: str | None = None) -> dict[str, Any]:
    flagged_ids = {item.instrument_id for item in scan.flagged_instruments}
    flagged_reason_map = {item.instrument_id: item.reasons for item in scan.flagged_instruments}
    average_daily_return_pct = _safe_decimal(scan.average_daily_return_pct)
    percentage_above_sma = _safe_decimal(scan.percentage_above_sma)
    contribution = (
        (average_daily_return_pct / Decimal("5")) + (percentage_above_sma / Decimal("100"))
    ).quantize(Decimal("0.000001"))
    return {
        "member_count": scan.member_count,
        "average_daily_return_pct": average_daily_return_pct,
        "average_volume_ratio": _safe_decimal(scan.average_volume_ratio),
        "percentage_above_sma": percentage_above_sma,
        "group_strength_contribution": contribution,
        "flagged_ids": flagged_ids,
        "flagged_reason_map": flagged_reason_map,
        "watchlist_name": watchlist_name,
    }


def _build_derivatives_context(session: Session, *, candidate_date: date) -> dict[str, Any]:
    features = (
        session.query(TwDerivativesFeature)
        .filter(TwDerivativesFeature.trade_date == candidate_date)
        .order_by(TwDerivativesFeature.id.asc())
        .all()
    )
    summary = generate_daily_institutional_bias_summary(candidate_date, features)
    return {
        "overall_regime": summary.overall_regime,
        "average_bias_score": summary.average_bias_score,
    }


def _scanner_memberships_for_instrument(
    *,
    instrument_id: int,
    tag_names: list[str],
    watchlists: list[dict[str, Any]],
    scanner_context: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    memberships: list[dict[str, Any]] = []
    for tag in tag_names:
        summary = scanner_context.get(f"tag:{tag}")
        if summary is None:
            continue
        memberships.append(
            {
                "kind": "tag",
                "name": tag,
                "group_strength_contribution": str(summary["group_strength_contribution"]),
                "average_volume_ratio": str(summary["average_volume_ratio"])
                if summary["average_volume_ratio"] is not None
                else None,
                "percentage_above_sma": str(summary["percentage_above_sma"]),
                "flagged": instrument_id in summary["flagged_ids"],
                "flag_reasons": summary["flagged_reason_map"].get(instrument_id, []),
            }
        )
    for watchlist in watchlists:
        summary = scanner_context.get(f"watchlist:{watchlist['id']}")
        if summary is None:
            continue
        memberships.append(
            {
                "kind": "watchlist",
                "name": watchlist["name"],
                "group_strength_contribution": str(summary["group_strength_contribution"]),
                "average_volume_ratio": str(summary["average_volume_ratio"])
                if summary["average_volume_ratio"] is not None
                else None,
                "percentage_above_sma": str(summary["percentage_above_sma"]),
                "flagged": instrument_id in summary["flagged_ids"],
                "flag_reasons": summary["flagged_reason_map"].get(instrument_id, []),
            }
        )
    return memberships


def _resolve_close_change_pct(bar: DailyBar) -> Decimal:
    if bar.change_percent is not None:
        return bar.change_percent.quantize(Decimal("0.000001"))
    if bar.open == 0:
        return Decimal("0.000000")
    return (((bar.close - bar.open) / bar.open) * Decimal("100")).quantize(Decimal("0.000001"))


def _safe_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.000000")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.000001"))
    return Decimal(str(value)).quantize(Decimal("0.000001"))


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
