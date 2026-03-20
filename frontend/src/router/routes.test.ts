import { describe, expect, it } from "vitest";

import { routes } from "@/router/routes";

describe("routes", () => {
  it("includes the expected top-level pages", () => {
    expect(routes.map((route) => route.name)).toEqual([
      "overview",
      "coverage",
      "operations",
      "watchlists",
      "groups",
      "stock-charts",
      "market-charts",
      "candidates",
      "reports",
      "backtests",
      "derivatives",
    ]);
  });

  it("defines frontend-facing labels and titles", () => {
    for (const route of routes) {
      expect(typeof route.meta?.label).toBe("string");
      expect(typeof route.meta?.title).toBe("string");
      expect(typeof route.meta?.description).toBe("string");
    }
  });
});
