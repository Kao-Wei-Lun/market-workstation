import { describe, expect, it } from "vitest";

import { buildReportRelatedLinks } from "@/utils/reports";

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
});
