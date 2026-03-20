export type Tone = "positive" | "negative" | "neutral" | "info";

export interface DashboardMeta {
  generated_at: string;
  as_of_date: string | null;
  is_empty: boolean;
  item_count: number;
  returned_count: number;
  limit: number | null;
  offset: number | null;
}

export interface DashboardSummaryCard {
  key: string;
  label: string;
  value: string;
  display_value: string;
  tone: Tone;
}

export interface DashboardRankedItem {
  key: string;
  label: string;
  primary_value: string;
  secondary_value: string | null;
  hint: string | null;
  metadata_json: Record<string, unknown>;
}

export interface DashboardRankedList {
  key: string;
  title: string;
  item_count: number;
  items: DashboardRankedItem[];
}

export interface DashboardViewBase {
  meta: DashboardMeta;
  summary_cards: DashboardSummaryCard[];
  highlights: string[];
  ranked_lists: DashboardRankedList[];
}

export interface GroupMemberChange {
  instrument_id: number;
  symbol: string;
  close_change_pct: string;
}

export interface GroupScannerFlaggedInstrument {
  instrument_id: number;
  symbol: string;
  close_change_pct: string;
  volume_ratio: string | null;
  above_sma: boolean | null;
  reasons: string[];
}

export interface GroupScannerRead {
  member_count: number;
  average_daily_return_pct: string;
  top_gainers: GroupMemberChange[];
  top_losers: GroupMemberChange[];
  average_volume_ratio: string | null;
  percentage_above_sma: string | null;
  flagged_instruments: GroupScannerFlaggedInstrument[];
}

export interface GroupSummaryRead {
  member_count: number;
  average_close_change_pct: string;
  top_gainers: GroupMemberChange[];
  top_losers: GroupMemberChange[];
  percentage_above_sma: string;
}

export interface WatchlistRead {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface WatchlistSummarySnapshotRead {
  watchlist: WatchlistRead;
  trade_date: string;
  summary: GroupSummaryRead;
  scanner: GroupScannerRead | null;
}

export interface GroupSummarySnapshotRead {
  tag: string;
  trade_date: string;
  summary: GroupSummaryRead;
  scanner: GroupScannerRead | null;
}

export interface CandidateRunRead {
  id: number;
  candidate_date: string;
  status: string;
  total_candidates: number;
  generation_config_json: Record<string, unknown>;
  summary_json: Record<string, unknown>;
  created_at: string;
}

export interface CandidateItemRead {
  id: number;
  run_id: number;
  instrument_id: number;
  candidate_date: string;
  symbol: string;
  score: string;
  rank: number;
  candidate_reasons: string[];
  supporting_metrics: Record<string, unknown>;
  created_at: string;
}

export interface CandidateSummarySnapshotRead {
  run: CandidateRunRead;
  top_items: CandidateItemRead[];
}

export interface DailyInstitutionalBiasSummary {
  trade_date: string;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  anomaly_count: number;
  average_bias_score: string;
  overall_regime: string;
  highlights: string[];
}

export interface BacktestRunRead {
  id: number;
  strategy_id: number;
  status: string;
  initial_cash: string;
  final_cash: string;
  total_return: string;
  total_return_pct: string;
  total_trades: number;
  win_rate: string;
  fee_paid: string;
  tax_paid: string;
  slippage_paid: string;
  resolved_parameters_json: Record<string, unknown>;
  metrics_json: Record<string, unknown>;
  notes: string | null;
  started_at: string;
  finished_at: string;
  created_at: string;
}

export interface BacktestTradeRead {
  id: number;
  run_id: number;
  instrument_id: number;
  entry_date: string;
  exit_date: string;
  entry_price: string;
  exit_price: string;
  quantity: number;
  gross_pnl: string;
  net_pnl: string;
  fee_paid: string;
  tax_paid: string;
  slippage_paid: string;
  holding_period_days: number;
  exit_reason: string;
  created_at: string;
}

export interface BacktestSummarySnapshotRead {
  latest_run: BacktestRunRead | null;
  recent_runs: BacktestRunRead[];
  recent_trades: BacktestTradeRead[];
}

export interface ReportDailyRead {
  id: number;
  report_date: string;
  report_type: string;
  report_key: string;
  title: string;
  content_json: Record<string, unknown>;
  markdown_text: string;
  created_at: string;
}

export interface ReportSummarySnapshotRead {
  reports: ReportDailyRead[];
}

export interface MarketSummaryContent {
  trade_date: string;
  instrument_count: number;
  advancers: number;
  decliners: number;
  unchanged: number;
  average_close_change_pct: string;
  percentage_above_sma20: string;
  top_gainers: GroupMemberChange[];
  top_losers: GroupMemberChange[];
}

export interface DashboardOverviewDataRead {
  market_snapshot: MarketSummaryContent | null;
  watchlist_summary: WatchlistSummarySnapshotRead | null;
  group_summary: GroupSummarySnapshotRead | null;
  candidate_summary: CandidateSummarySnapshotRead | null;
  derivatives_summary: DailyInstitutionalBiasSummary | null;
  backtest_summary: BacktestSummarySnapshotRead | null;
  report_summary: ReportSummarySnapshotRead | null;
}

export interface DashboardOverviewRead extends DashboardViewBase {
  data: DashboardOverviewDataRead;
}

export interface WatchlistDashboardRead extends DashboardViewBase {
  data: WatchlistSummarySnapshotRead | null;
}

export interface GroupDashboardRead extends DashboardViewBase {
  data: GroupSummarySnapshotRead | null;
}

export interface CandidatesDashboardRead extends DashboardViewBase {
  data: CandidateSummarySnapshotRead | null;
}

export interface DerivativesDashboardRead extends DashboardViewBase {
  data: DailyInstitutionalBiasSummary | null;
}

export interface BacktestsDashboardRead extends DashboardViewBase {
  data: BacktestSummarySnapshotRead | null;
}

export interface ReportsDashboardRead extends DashboardViewBase {
  data: ReportSummarySnapshotRead | null;
}
