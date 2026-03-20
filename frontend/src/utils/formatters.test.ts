import { describe, expect, it } from "vitest";

import { formatDate, formatNumber, formatTitle } from "@/utils/formatters";

describe("formatters", () => {
  it("formats numbers and falls back safely", () => {
    expect(formatNumber("1234.5")).toBe("1,234.5");
    expect(formatNumber(null)).toBe("n/a");
  });

  it("formats dates and titles", () => {
    expect(formatDate("2024-01-05T12:34:56")).toBe("2024-01-05");
    expect(formatTitle("daily_report_bundle")).toBe("Daily Report Bundle");
  });
});
