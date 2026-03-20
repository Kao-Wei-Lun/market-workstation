import { describe, expect, it } from "vitest";

import { normalizeCandidateItem } from "@/api/candidates";

describe("candidate api normalization", () => {
  it("maps aliased backend candidate fields into the frontend shape", () => {
    const normalized = normalizeCandidateItem({
      id: 1,
      run_id: 2,
      instrument_id: 3,
      candidate_date: "2026-03-20",
      symbol: "2330",
      score: "91.5",
      rank: 1,
      candidate_reasons_json: ["above_sma20", "group_strength"],
      supporting_metrics_json: { score_components: { technical: 45 } },
      created_at: "2026-03-20T08:00:00",
    });

    expect(normalized.candidate_reasons).toEqual(["above_sma20", "group_strength"]);
    expect(normalized.supporting_metrics).toEqual({ score_components: { technical: 45 } });
  });

  it("falls back to empty structures when optional arrays or objects are missing", () => {
    const normalized = normalizeCandidateItem({
      id: 1,
      run_id: 2,
      instrument_id: 3,
      candidate_date: "2026-03-20",
      symbol: "AAPL",
      score: "77.0",
      rank: 2,
      created_at: "2026-03-20T08:00:00",
    });

    expect(normalized.candidate_reasons).toEqual([]);
    expect(normalized.supporting_metrics).toEqual({});
  });
});
