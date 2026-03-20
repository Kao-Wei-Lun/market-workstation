import type { DashboardMeta, DashboardSummaryCard } from "@/types/dashboard";
import type { IngestJobRead } from "@/types/api";

export interface UniversePresetSummaryRead {
  preset_name: string;
  description: string;
  available_presets: string[];
  configured_instrument_count: number;
  configured_watchlist_count: number;
  scopes_declared: number;
}

export interface UniverseScopeCoverageRead {
  key: string;
  label: string;
  market: string;
  asset_type: string;
  source_route: string;
  coverage: string;
  description: string;
  configured_instrument_count: number;
  loaded_instrument_count: number;
  configured_watchlist_count: number;
  loaded_watchlist_count: number;
  sample_symbols: string[];
}

export interface InstrumentCategoryCountRead {
  category_type: "market" | "asset_type" | "source_route";
  key: string;
  label: string;
  instrument_count: number;
}

export interface UniverseCoverageDataRead {
  preset: UniversePresetSummaryRead;
  scopes: UniverseScopeCoverageRead[];
  market_counts: InstrumentCategoryCountRead[];
  asset_type_counts: InstrumentCategoryCountRead[];
  source_route_counts: InstrumentCategoryCountRead[];
}

export interface UniverseCoverageRead {
  meta: DashboardMeta;
  summary_cards: DashboardSummaryCard[];
  highlights: string[];
  data: UniverseCoverageDataRead;
}

export interface DatasetFreshnessRead {
  dataset_key: string;
  label: string;
  latest_date: string | null;
  record_count: number;
  status: "ready" | "missing";
}

export interface JobStatusCountRead {
  status: string;
  count: number;
}

export interface WorkerStatusRead {
  worker_name: string;
  worker_role: string;
  status: string;
  heartbeat_at: string;
  stale: boolean;
  last_job_name: string | null;
  last_job_status: string | null;
  last_error: string | null;
}

export interface SystemStatusDataRead {
  datasets: DatasetFreshnessRead[];
  recent_jobs: IngestJobRead[];
  job_status_counts: JobStatusCountRead[];
  workers: WorkerStatusRead[];
}

export interface SystemStatusRead {
  meta: DashboardMeta;
  summary_cards: DashboardSummaryCard[];
  highlights: string[];
  data: SystemStatusDataRead;
}
