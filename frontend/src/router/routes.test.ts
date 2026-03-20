import { describe, expect, it } from "vitest";

import { routes } from "@/router/routes";

describe("routes", () => {
  it("includes the expected top-level pages", () => {
    expect(routes.map((route) => route.name)).toEqual([
      "overview",
      "watchlists",
      "groups",
      "candidates",
      "reports",
      "backtests",
      "derivatives",
    ]);
  });
});
