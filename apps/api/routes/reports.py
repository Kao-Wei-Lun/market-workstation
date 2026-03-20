from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from services.core.reports.service import (
    export_report_bundle,
    get_latest_report_date,
    get_report,
    get_report_bundle,
    get_report_section,
    list_reports,
)
from services.db.session import get_db_session
from services.schemas.reporting import DailyReportBundleContent, ReportDailyRead, ReportSectionRead

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/latest", response_model=list[ReportDailyRead])
async def list_latest_reports_route(
    report_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[ReportDailyRead]:
    latest_date = get_latest_report_date(session, report_type=report_type)
    if latest_date is None:
        return []
    reports = list_reports(session, report_date=latest_date, report_type=report_type, limit=limit)
    return [ReportDailyRead.model_validate(report) for report in reports]


@router.get("/{report_date}/bundle", response_model=DailyReportBundleContent)
async def get_report_bundle_route(
    report_date: date,
    session: Session = Depends(get_db_session),
) -> DailyReportBundleContent:
    bundle = get_report_bundle(session, report_date=report_date)
    if bundle is None:
        raise HTTPException(status_code=404, detail="report bundle not found")
    return bundle


@router.get("/{report_date}/bundle/export")
async def export_report_bundle_route(
    report_date: date,
    export_format: Literal["json", "csv"] = Query(default="json"),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        file_name, content = export_report_bundle(session, report_date=report_date, export_format=export_format)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    media_type = "application/json" if export_format == "json" else "text/csv"
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})


@router.get("/{report_date}/bundle/sections/{section_type}", response_model=ReportSectionRead)
async def get_report_section_route(
    report_date: date,
    section_type: str,
    session: Session = Depends(get_db_session),
) -> ReportSectionRead:
    section = get_report_section(session, report_date=report_date, section_type=section_type)
    if section is None:
        raise HTTPException(status_code=404, detail="report section not found")
    return section


@router.get("/{report_date}/{report_type}", response_model=ReportDailyRead)
async def get_report_route(
    report_date: date,
    report_type: str,
    report_key: str = Query(default=""),
    session: Session = Depends(get_db_session),
) -> ReportDailyRead:
    report = get_report(
        session,
        report_date=report_date,
        report_type=report_type,
        report_key=report_key,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return ReportDailyRead.model_validate(report)


@router.get("", response_model=list[ReportDailyRead])
async def list_reports_route(
    report_date: date | None = None,
    report_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[ReportDailyRead]:
    reports = list_reports(session, report_date=report_date, report_type=report_type, limit=limit)
    return [ReportDailyRead.model_validate(report) for report in reports]
