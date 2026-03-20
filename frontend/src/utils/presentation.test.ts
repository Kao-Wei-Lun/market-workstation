import { describe, expect, it } from "vitest";

import { buildChartPoints, filterRowsByQuery, sortRows } from "@/utils/presentation";

describe("presentation utils", () => {
  it("sorts rows by numeric-like values", () => {
    const rows = [
      { symbol: "AAPL", score: "12.5" },
      { symbol: "2330", score: "19.2" },
      { symbol: "MSFT", score: "5.3" },
    ];

    expect(sortRows(rows, "score", "desc").map((row) => row.symbol)).toEqual(["2330", "AAPL", "MSFT"]);
  });

  it("filters rows by text query across selected fields", () => {
    const rows = [
      { symbol: "2330", reasons: "trend,strong" },
      { symbol: "AAPL", reasons: "watchlist" },
    ];

    expect(filterRowsByQuery(rows, ["symbol", "reasons"], "trend")).toEqual([rows[0]]);
  });

  it("normalizes chart points to percentages", () => {
    const points = buildChartPoints([
      { label: "Bullish", value: 10 },
      { label: "Bearish", value: 5 },
    ]);

    expect(points[0].percentage).toBe(100);
    expect(points[1].percentage).toBe(50);
  });
});
