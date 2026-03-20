import { getJson } from "@/api/http";
import type { DailyReportBundleContent, ReportSectionRead } from "@/types/api";
import type { ReportDailyRead } from "@/types/dashboard";

export async function fetchLatestReports(params: { reportType?: string; limit?: number } = {}): Promise<ReportDailyRead[]> {
  return getJson<ReportDailyRead[]>("/reports/latest", {
    params: {
      report_type: params.reportType,
      limit: params.limit,
    },
  });
}

export async function fetchReports(params: { reportDate?: string; reportType?: string; limit?: number } = {}): Promise<ReportDailyRead[]> {
  return getJson<ReportDailyRead[]>("/reports", {
    params: {
      report_date: params.reportDate,
      report_type: params.reportType,
      limit: params.limit,
    },
  });
}

export async function fetchReportBundle(reportDate: string): Promise<DailyReportBundleContent> {
  return getJson<DailyReportBundleContent>(`/reports/${reportDate}/bundle`);
}

export async function fetchReportSection(reportDate: string, sectionType: string): Promise<ReportSectionRead> {
  return getJson<ReportSectionRead>(`/reports/${reportDate}/bundle/sections/${sectionType}`);
}
