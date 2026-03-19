from services.schemas.etl import NormalizedDataBatch, ValidationIssue, ValidationResult


def validate_normalized_batch(batch: NormalizedDataBatch) -> ValidationResult:
    issues: list[ValidationIssue] = []

    seen_daily_bar_keys: set[tuple[int | None, str, object]] = set()
    for daily_bar in batch.daily_bars:
        daily_bar_key = (daily_bar.instrument_id, daily_bar.symbol, daily_bar.trade_date)
        if daily_bar_key in seen_daily_bar_keys:
            issues.append(
                ValidationIssue(message=f"duplicate daily bar for {daily_bar.symbol} {daily_bar.trade_date}")
            )
        seen_daily_bar_keys.add(daily_bar_key)
        if daily_bar.volume < 0:
            issues.append(
                ValidationIssue(message=f"negative volume for {daily_bar.symbol} {daily_bar.trade_date}")
            )

    seen_series_keys: set[tuple[str, object]] = set()
    for series_point in batch.series_points:
        series_point_key = (series_point.series_key, series_point.trade_date)
        if series_point_key in seen_series_keys:
            issues.append(
                ValidationIssue(
                    message=(
                        f"duplicate series point for {series_point.series_key} {series_point.trade_date}"
                    )
                )
            )
        seen_series_keys.add(series_point_key)

    return ValidationResult(issues=issues)
