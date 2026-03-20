import type { CandidateItemRead } from "@/types/dashboard";

export interface CandidateScoreMetric {
  label: string;
  value: string;
  hint: string;
}

export interface CandidateScannerMembershipView {
  kind: string;
  name: string;
  flagged: boolean;
  flagReasons: string[];
  groupStrengthContribution: string | null;
  averageVolumeRatio: string | null;
  percentageAboveSma: string | null;
}

export interface CandidateDetailView {
  reasons: string[];
  tags: string[];
  watchlists: string[];
  scoreBreakdown: CandidateScoreMetric[];
  keyMetrics: CandidateScoreMetric[];
  scannerMemberships: CandidateScannerMembershipView[];
}

const SCORE_LABELS: Record<string, string> = {
  technical_score: "技術分",
  momentum_score: "動能分",
  group_strength_score: "群組強度",
  watchlist_bonus: "觀察清單加分",
  derivatives_context_bonus: "衍生性商品脈絡",
};

const METRIC_LABELS: Record<string, string> = {
  close: "收盤價",
  change_percent: "單日漲跌幅",
  sma20: "SMA20",
  rsi14: "RSI14",
  macd_histogram: "MACD Histogram",
  average_group_volume_ratio: "平均群組量比",
  derivatives_regime: "衍生性商品 regime",
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : String(item)))
    .filter((item) => item.length > 0);
}

function getString(value: unknown): string | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  return String(value);
}

function buildMetric(label: string, value: unknown, hint: string): CandidateScoreMetric | null {
  const normalized = getString(value);
  if (!normalized) {
    return null;
  }
  return { label, value: normalized, hint };
}

export function buildCandidateDetailView(item: CandidateItemRead): CandidateDetailView {
  const metrics = asRecord(item.supporting_metrics) ?? {};
  const scannerMemberships = Array.isArray(metrics.scanner_memberships) ? metrics.scanner_memberships : [];
  const scoreBreakdown = Object.entries(SCORE_LABELS)
    .map(([key, label]) => buildMetric(label, metrics[key], "評分拆解"))
    .filter((metric): metric is CandidateScoreMetric => metric !== null);
  const keyMetrics = Object.entries(METRIC_LABELS)
    .map(([key, label]) => buildMetric(label, metrics[key], "支援指標"))
    .filter((metric): metric is CandidateScoreMetric => metric !== null);

  return {
    reasons: Array.isArray(item.candidate_reasons) ? item.candidate_reasons : [],
    tags: asStringArray(metrics.tags),
    watchlists: asStringArray(metrics.watchlists),
    scoreBreakdown,
    keyMetrics,
    scannerMemberships: scannerMemberships
      .map((membership) => {
        const record = asRecord(membership);
        if (!record) {
          return null;
        }
        return {
          kind: getString(record.kind) ?? "unknown",
          name: getString(record.name) ?? "未命名",
          flagged: Boolean(record.flagged),
          flagReasons: asStringArray(record.flag_reasons),
          groupStrengthContribution: getString(record.group_strength_contribution),
          averageVolumeRatio: getString(record.average_volume_ratio),
          percentageAboveSma: getString(record.percentage_above_sma),
        };
      })
      .filter((membership): membership is CandidateScannerMembershipView => membership !== null),
  };
}
