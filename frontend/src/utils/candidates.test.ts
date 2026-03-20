import { describe, expect, it } from "vitest";

import { buildCandidateDetailView } from "@/utils/candidates";

describe("candidate detail helpers", () => {
  it("extracts score breakdown, tags, watchlists, and scanner memberships", () => {
    const detail = buildCandidateDetailView({
      id: 1,
      run_id: 2,
      instrument_id: 3,
      candidate_date: "2026-03-20",
      symbol: "2330",
      score: "6.750000",
      rank: 1,
      candidate_reasons: ["close_above_sma20", "watchlist_member"],
      supporting_metrics: {
        technical_score: "3.000000",
        momentum_score: "1.000000",
        group_strength_score: "2.000000",
        watchlist_bonus: "0.750000",
        derivatives_context_bonus: "0.000000",
        close: "1010",
        sma20: "980",
        tags: ["semiconductor", "sample"],
        watchlists: ["sample-core"],
        scanner_memberships: [
          {
            kind: "tag",
            name: "semiconductor",
            flagged: true,
            flag_reasons: ["high_volume"],
            group_strength_contribution: "2.000000",
            average_volume_ratio: "1.500000",
            percentage_above_sma: "75.000000",
          },
        ],
      },
      created_at: "2026-03-20T08:00:00",
    });

    expect(detail.reasons).toEqual(["close_above_sma20", "watchlist_member"]);
    expect(detail.tags).toEqual(["semiconductor", "sample"]);
    expect(detail.watchlists).toEqual(["sample-core"]);
    expect(detail.scoreBreakdown.map((item) => item.label)).toContain("技術分");
    expect(detail.keyMetrics.map((item) => item.label)).toContain("收盤價");
    expect(detail.scannerMemberships[0]).toMatchObject({
      kind: "tag",
      name: "semiconductor",
      flagged: true,
      flagReasons: ["high_volume"],
    });
  });

  it("falls back to empty sections when optional context is missing", () => {
    const detail = buildCandidateDetailView({
      id: 1,
      run_id: 2,
      instrument_id: 3,
      candidate_date: "2026-03-20",
      symbol: "AAPL",
      score: "4.000000",
      rank: 2,
      candidate_reasons: [],
      supporting_metrics: {},
      created_at: "2026-03-20T08:00:00",
    });

    expect(detail.tags).toEqual([]);
    expect(detail.watchlists).toEqual([]);
    expect(detail.scannerMemberships).toEqual([]);
  });
});
