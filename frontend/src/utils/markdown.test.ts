import { describe, expect, it } from "vitest";

import { parseMarkdownBlocks } from "@/utils/markdown";

describe("markdown parsing helpers", () => {
  it("splits headings, paragraphs, and list items into renderable blocks", () => {
    const blocks = parseMarkdownBlocks(`# 標題

第一段文字。

- 第一點
- 第二點

## 子標題
第二段文字。`);

    expect(blocks).toEqual([
      { key: "heading-0", type: "heading", level: 1, text: "標題" },
      { key: "paragraph-1", type: "paragraph", text: "第一段文字。" },
      { key: "list-2", type: "list", items: ["第一點", "第二點"] },
      { key: "heading-3", type: "heading", level: 2, text: "子標題" },
      { key: "paragraph-4", type: "paragraph", text: "第二段文字。" },
    ]);
  });
});
