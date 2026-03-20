import { http } from "@/api/http";
import type {
  BacktestsDashboardRead,
  CandidatesDashboardRead,
  DashboardOverviewRead,
  DerivativesDashboardRead,
  GroupDashboardRead,
  ReportsDashboardRead,
  WatchlistDashboardRead,
  WatchlistRead,
} from "@/types/dashboard";

interface OverviewParams {
  tradeDate?: string;
  watchlistId?: number;
  tag?: string;
  topN?: number;
}

export async function fetchOverview(params: OverviewParams = {}): Promise<DashboardOverviewRead> {
  const response = await http.get<DashboardOverviewRead>("/api/dashboard/overview", {
    params: {
      trade_date: params.tradeDate,
      watchlist_id: params.watchlistId,
      tag: params.tag,
      top_n: params.topN,
    },
  });
  return response.data;
}

export async function fetchWatchlists(): Promise<WatchlistRead[]> {
  const response = await http.get<WatchlistRead[]>("/watchlists");
  return response.data;
}

export async function fetchWatchlistDashboard(
  watchlistId: number,
  params: { tradeDate?: string; topN?: number } = {},
): Promise<WatchlistDashboardRead> {
  const response = await http.get<WatchlistDashboardRead>(`/api/dashboard/watchlists/${watchlistId}`, {
    params: {
      trade_date: params.tradeDate,
      top_n: params.topN,
    },
  });
  return response.data;
}

export async function fetchGroupDashboard(
  tag: string,
  params: { tradeDate?: string; topN?: number } = {},
): Promise<GroupDashboardRead> {
  const response = await http.get<GroupDashboardRead>(`/api/dashboard/groups/${encodeURIComponent(tag)}`, {
    params: {
      trade_date: params.tradeDate,
      top_n: params.topN,
    },
  });
  return response.data;
}

export async function fetchCandidatesDashboard(params: {
  candidateDate?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<CandidatesDashboardRead> {
  const response = await http.get<CandidatesDashboardRead>("/api/dashboard/candidates/latest", {
    params: {
      candidate_date: params.candidateDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
  return response.data;
}

export async function fetchDerivativesDashboard(tradeDate?: string): Promise<DerivativesDashboardRead> {
  const response = await http.get<DerivativesDashboardRead>("/api/dashboard/derivatives/latest", {
    params: { trade_date: tradeDate },
  });
  return response.data;
}

export async function fetchBacktestsDashboard(limit = 5): Promise<BacktestsDashboardRead> {
  const response = await http.get<BacktestsDashboardRead>("/api/dashboard/backtests/latest", {
    params: { limit },
  });
  return response.data;
}

export async function fetchReportsDashboard(params: {
  reportDate?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<ReportsDashboardRead> {
  const response = await http.get<ReportsDashboardRead>("/api/dashboard/reports/latest", {
    params: {
      report_date: params.reportDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
  return response.data;
}
