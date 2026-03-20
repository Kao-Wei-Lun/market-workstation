import { describe, expect, it } from "vitest";

import { formatDate, formatDateTime, formatList, formatNumber, formatPercent, formatTitle } from "@/utils/formatters";

describe("formatters", () => {
  it("formats numbers and falls back safely", () => {
    expect(formatNumber("1234.5")).toBe("1,234.5");
    expect(formatNumber(null)).toBe("n/a");
  });

  it("formats dates and titles", () => {
    expect(formatDate("2024-01-05T12:34:56")).toBe("2024-01-05");
    expect(formatDateTime("2024-01-05T12:34:56")).toBe("2024-01-05 12:34");
    expect(formatPercent("12.345")).toBe("12.35%");
    expect(formatTitle("daily_report_bundle")).toBe("Daily Report Bundle");
  });

  it("formats optional lists safely", () => {
    expect(formatList(["alpha", "beta"])).toBe("alpha, beta");
    expect(formatList([])).toBe("n/a");
    expect(formatList(undefined, "No reasons")).toBe("No reasons");
  });
});
