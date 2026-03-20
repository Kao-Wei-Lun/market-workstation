import { describe, expect, it } from "vitest";

import { buildDateRange, buildOverlayLines, describeAnnotation, formatFlowHighlight } from "@/utils/charts";

describe("charts utils", () => {
  it("builds overlay lines from indicator series", () => {
    const lines = buildOverlayLines([
      {
        indicator_name: "sma",
        component: "value",
        parameter_signature: "period=20",
        points: [{ trade_date: "2024-01-01", value: "100.5" }],
      },
    ]);
    expect(lines).toHaveLength(1);
    expect(lines[0].points[0].value).toBe(100.5);
  });

  it("builds a date range from latest date", () => {
    const range = buildDateRange("2024-01-31", 30);
    expect(range.dateTo).toBe("2024-01-31");
    expect(range.dateFrom).toBe("2024-01-01");
  });

  it("formats annotation and flow copy", () => {
    expect(
      describeAnnotation({
        id: 1,
        instrument_id: 1,
        symbol_snapshot: "2330",
        view_kind: "instrument",
        annotation_type: "horizontal_line",
        timeframe: "1d",
        label: "壓力",
        payload_json: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      }),
    ).toContain("水平線");
    expect(
      formatFlowHighlight({
        trade_date: "2024-01-01",
        futures_net_open_interest: 100,
        futures_net_amount: "1",
        options_net_open_interest: 50,
        options_net_amount: "1",
        average_bias_score: "1.2",
        bullish_count: 1,
        bearish_count: 0,
        anomaly_count: 0,
      }),
    ).toContain("期貨淨未平倉");
  });
});
