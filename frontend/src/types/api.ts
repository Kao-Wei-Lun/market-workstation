import type {
  BacktestRunRead,
  BacktestTradeRead,
  CandidateItemRead,
  CandidateRunRead,
  DailyInstitutionalBiasSummary,
  GroupSummaryRead,
  ReportDailyRead,
  WatchlistRead,
} from "@/types/dashboard";

export interface WatchlistItemRead {
  id: number;
  watchlist_id: number;
  instrument_id: number;
  created_at: string;
}

export interface ReportSectionRead {
  title: string;
  section_type: string;
  markdown_body: string;
  payload_json: Record<string, unknown>;
}

export interface DailyReportBundleMetadata {
  report_date: string;
  bundle_version: string;
  section_count: number;
  strongest_group_name: string | null;
  weakest_group_name: string | null;
  strongest_watchlist_name: string | null;
  weakest_watchlist_name: string | null;
  top_candidate_symbols: string[];
}

export interface DailyReportBundleContent {
  report_date: string;
  metadata: DailyReportBundleMetadata;
  sections: ReportSectionRead[];
}

export interface CandidateRunWithItemsRead {
  run: CandidateRunRead;
  items: CandidateItemRead[];
}

export interface BacktestCreateResponse {
  run: BacktestRunRead;
  trades: BacktestTradeRead[];
}

export interface LatestDerivativesSummaryRead extends DailyInstitutionalBiasSummary {}

export interface LatestReportsRead extends Array<ReportDailyRead> {}

export interface LatestWatchlistSummaryRead {
  watchlist: WatchlistRead;
  trade_date: string;
  summary: GroupSummaryRead;
}
