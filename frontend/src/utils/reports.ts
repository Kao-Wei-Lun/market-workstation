import type { RouteLocationRaw } from "vue-router";

import type { DailyReportBundleContent, ReportSectionRead } from "@/types/api";

export interface ReportRelatedLink {
  label: string;
  to: RouteLocationRaw;
}

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

function getNumber(value: unknown): number | null {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
}

export function buildReportRelatedLinks(
  bundle: DailyReportBundleContent | null,
  section: ReportSectionRead | null,
): ReportRelatedLink[] {
  if (!bundle) {
    return [];
  }

  const links: ReportRelatedLink[] = [];
  const seen = new Set<string>();
  const payload = asRecord(section?.payload_json) ?? {};

  function push(label: string, to: RouteLocationRaw): void {
    const key = `${label}:${JSON.stringify(to)}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    links.push({ label, to });
  }

  const tag = getString(payload.tag);
  if (tag) {
    push(`查看群組 ${tag}`, { name: "groups", query: { tag, tradeDate: bundle.report_date } });
  }

  const watchlistId = getNumber(payload.watchlist_id);
  const watchlistName = getString(payload.watchlist_name);
  if (watchlistId !== null) {
    push(`查看觀察清單${watchlistName ? ` ${watchlistName}` : ""}`, {
      name: "watchlists",
      query: { watchlistId: String(watchlistId), tradeDate: bundle.report_date },
    });
  }

  const candidateSymbols = [
    ...bundle.metadata.top_candidate_symbols,
    ...asStringArray(payload.top_candidate_symbols),
    ...asStringArray(payload.candidate_symbols),
  ];
  for (const symbol of candidateSymbols.slice(0, 3)) {
    push(`查看候選 ${symbol}`, {
      name: "candidates",
      query: { candidateDate: bundle.report_date, search: symbol },
    });
  }

  const strongestGroup = bundle.metadata.strongest_group_name;
  if (strongestGroup) {
    push(`查看強勢群組 ${strongestGroup}`, {
      name: "groups",
      query: { tag: strongestGroup, tradeDate: bundle.report_date },
    });
  }
  const weakestGroup = bundle.metadata.weakest_group_name;
  if (weakestGroup) {
    push(`查看弱勢群組 ${weakestGroup}`, {
      name: "groups",
      query: { tag: weakestGroup, tradeDate: bundle.report_date },
    });
  }

  const summary = asRecord(payload.summary);
  const overallRegime = getString(summary?.overall_regime);
  if (overallRegime) {
    push(`查看衍生性商品摘要`, {
      name: "derivatives",
      query: { tradeDate: bundle.report_date, regime: overallRegime },
    });
  }

  return links;
}
