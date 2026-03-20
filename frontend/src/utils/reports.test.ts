import { describe, expect, it } from "vitest";

import { buildReportRelatedLinks, buildReportSectionMetrics, listAvailableReportTypes } from "@/utils/reports";

describe("report related link helpers", () => {
  it("builds cross-page links from bundle metadata and section payload", () => {
    const links = buildReportRelatedLinks(
      {
        report_date: "2026-03-20",
        metadata: {
          report_date: "2026-03-20",
          bundle_version: "v1",
          section_count: 6,
          strongest_group_name: "semiconductor",
          weakest_group_name: "macro",
          strongest_watchlist_name: "focus",
          weakest_watchlist_name: null,
          top_candidate_symbols: ["2330", "AAPL"],
        },
        sections: [],
      },
      {
        title: "群組摘要",
        section_type: "group_summary",
        markdown_body: "demo",
        payload_json: {
          tag: "semiconductor",
          watchlist_id: 5,
          watchlist_name: "focus",
          summary: {
            overall_regime: "bullish",
          },
        },
      },
    );

    expect(links.map((link) => link.label)).toEqual(
      expect.arrayContaining([
        "查看群組 semiconductor",
        "查看觀察清單 focus",
        "查看候選 2330",
        "查看強勢群組 semiconductor",
        "查看弱勢群組 macro",
        "查看衍生性商品摘要",
      ]),
    );
  });

  it("returns an empty list when no bundle is available", () => {
    expect(buildReportRelatedLinks(null, null)).toEqual([]);
  });

  it("builds section metrics and unique report types for the reports page", () => {
    const bundle = {
      report_date: "2026-03-20",
      metadata: {
        report_date: "2026-03-20",
        bundle_version: "v1",
        section_count: 2,
        strongest_group_name: "semiconductor",
        weakest_group_name: null,
        strongest_watchlist_name: null,
        weakest_watchlist_name: null,
        top_candidate_symbols: ["2330"],
      },
      sections: [
        {
          title: "市場摘要",
          section_type: "market_summary",
          markdown_body: "# 市場摘要\n\n- 上漲 10\n- 下跌 5",
          payload_json: { trade_date: "2026-03-20", instrument_count: 20 },
        },
        {
          title: "候選摘要",
          section_type: "next_day_candidates",
          markdown_body: "# 候選摘要",
          payload_json: { candidate_symbols: ["2330"] },
        },
      ],
    };

    const metrics = buildReportSectionMetrics(bundle, bundle.sections[0], 2);
    const reportTypes = listAvailableReportTypes([
      {
        id: 1,
        report_date: "2026-03-20",
        report_type: "daily_report_bundle",
        report_key: "daily",
        title: "Daily",
        content_json: {},
        markdown_text: "demo",
        created_at: "2026-03-20T08:00:00",
      },
      {
        id: 2,
        report_date: "2026-03-20",
        report_type: "market_summary",
        report_key: "market",
        title: "Market",
        content_json: {},
        markdown_text: "demo",
        created_at: "2026-03-20T08:05:00",
      },
      {
        id: 3,
        report_date: "2026-03-20",
        report_type: "market_summary",
        report_key: "market-2",
        title: "Market 2",
        content_json: {},
        markdown_text: "demo",
        created_at: "2026-03-20T08:10:00",
      },
    ]);

    expect(metrics.map((item) => item.label)).toEqual(
      expect.arrayContaining(["報表日期", "目前區塊", "內容行數", "結構欄位數", "相關導頁"]),
    );
    expect(reportTypes).toEqual(["daily_report_bundle", "market_summary"]);
  });
});
