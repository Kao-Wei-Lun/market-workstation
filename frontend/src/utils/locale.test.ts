import { describe, expect, it } from "vitest";

import { t, toneLabel } from "@/utils/locale";

describe("locale helpers", () => {
  it("translates known UI strings into zh-TW", () => {
    expect(t("Overview")).toBe("總覽");
    expect(t("No items available.")).toBe("目前沒有可顯示的資料。");
  });

  it("falls back cleanly for unknown text and tone labels", () => {
    expect(t("自訂文字")).toBe("自訂文字");
    expect(toneLabel("positive")).toBe("偏多");
  });
});
