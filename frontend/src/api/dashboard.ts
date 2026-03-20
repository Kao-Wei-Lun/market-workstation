import { getJson } from "@/api/http";
import { normalizeCandidateItem } from "@/api/candidates";
import type { CandidateSummarySnapshotApiRead } from "@/types/api";
import type {
  BacktestsDashboardRead,
  CandidatesDashboardRead,
  DashboardOverviewRead,
  DerivativesDashboardRead,
  GroupDashboardRead,
  ReportsDashboardRead,
  WatchlistDashboardRead,
} from "@/types/dashboard";

interface OverviewParams {
  tradeDate?: string;
  watchlistId?: number;
  tag?: string;
  topN?: number;
}

export async function fetchOverview(params: OverviewParams = {}): Promise<DashboardOverviewRead> {
  const response = await getJson<DashboardOverviewRead>("/api/dashboard/overview", {
    params: {
      trade_date: params.tradeDate,
      watchlist_id: params.watchlistId,
      tag: params.tag,
      top_n: params.topN,
    },
  });
  return normalizeOverviewDashboard(response);
}

export async function fetchWatchlistDashboard(
  watchlistId: number,
  params: { tradeDate?: string; topN?: number } = {},
): Promise<WatchlistDashboardRead> {
  return getJson<WatchlistDashboardRead>(`/api/dashboard/watchlists/${watchlistId}`, {
    params: {
      trade_date: params.tradeDate,
      top_n: params.topN,
    },
  });
}

export async function fetchGroupDashboard(
  tag: string,
  params: { tradeDate?: string; topN?: number } = {},
): Promise<GroupDashboardRead> {
  return getJson<GroupDashboardRead>(`/api/dashboard/groups/${encodeURIComponent(tag)}`, {
    params: {
      trade_date: params.tradeDate,
      top_n: params.topN,
    },
  });
}

export async function fetchCandidatesDashboard(params: {
  candidateDate?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<CandidatesDashboardRead> {
  const response = await getJson<CandidatesDashboardRead>("/api/dashboard/candidates/latest", {
    params: {
      candidate_date: params.candidateDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
  return normalizeCandidatesDashboard(response);
}

export async function fetchDerivativesDashboard(tradeDate?: string): Promise<DerivativesDashboardRead> {
  return getJson<DerivativesDashboardRead>("/api/dashboard/derivatives/latest", {
    params: { trade_date: tradeDate },
  });
}

export async function fetchBacktestsDashboard(limit = 5): Promise<BacktestsDashboardRead> {
  return getJson<BacktestsDashboardRead>("/api/dashboard/backtests/latest", {
    params: { limit },
  });
}

export async function fetchReportsDashboard(params: {
  reportDate?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<ReportsDashboardRead> {
  return getJson<ReportsDashboardRead>("/api/dashboard/reports/latest", {
    params: {
      report_date: params.reportDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
}

function normalizeOverviewDashboard(response: DashboardOverviewRead): DashboardOverviewRead {
  if (!response.data.candidate_summary) {
    return response;
  }
  return {
    ...response,
    data: {
      ...response.data,
      candidate_summary: normalizeCandidateSummarySnapshot(response.data.candidate_summary as CandidateSummarySnapshotApiRead),
    },
  };
}

function normalizeCandidatesDashboard(response: CandidatesDashboardRead): CandidatesDashboardRead {
  if (!response.data) {
    return response;
  }
  return {
    ...response,
    data: normalizeCandidateSummarySnapshot(response.data as CandidateSummarySnapshotApiRead),
  };
}

function normalizeCandidateSummarySnapshot(snapshot: CandidateSummarySnapshotApiRead) {
  return {
    ...snapshot,
    top_items: (snapshot.top_items ?? []).map(normalizeCandidateItem),
  };
}
