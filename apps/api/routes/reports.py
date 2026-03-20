from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.core.reports.service import get_report, get_report_bundle, get_report_section, list_reports
from services.db.session import get_db_session
from services.schemas.reporting import DailyReportBundleContent, ReportDailyRead, ReportSectionRead

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_date}/bundle", response_model=DailyReportBundleContent)
async def get_report_bundle_route(
    report_date: date,
    session: Session = Depends(get_db_session),
) -> DailyReportBundleContent:
    bundle = get_report_bundle(session, report_date=report_date)
    if bundle is None:
        raise HTTPException(status_code=404, detail="report bundle not found")
    return bundle


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
    report_date: date,
    report_type: str | None = None,
    session: Session = Depends(get_db_session),
) -> list[ReportDailyRead]:
    reports = list_reports(session, report_date=report_date, report_type=report_type)
    return [ReportDailyRead.model_validate(report) for report in reports]
