export interface MarkdownBlockBase {
  key: string;
  type: "heading" | "paragraph" | "list";
}

export interface MarkdownHeadingBlock extends MarkdownBlockBase {
  type: "heading";
  level: number;
  text: string;
}

export interface MarkdownParagraphBlock extends MarkdownBlockBase {
  type: "paragraph";
  text: string;
}

export interface MarkdownListBlock extends MarkdownBlockBase {
  type: "list";
  items: string[];
}

export type MarkdownBlock = MarkdownHeadingBlock | MarkdownParagraphBlock | MarkdownListBlock;

export function parseMarkdownBlocks(input: string): MarkdownBlock[] {
  const lines = input.split("\n");
  const blocks: MarkdownBlock[] = [];
  let paragraphBuffer: string[] = [];
  let listBuffer: string[] = [];

  function flushParagraph(): void {
    if (!paragraphBuffer.length) {
      return;
    }
    blocks.push({
      key: `paragraph-${blocks.length}`,
      type: "paragraph",
      text: paragraphBuffer.join(" "),
    });
    paragraphBuffer = [];
  }

  function flushList(): void {
    if (!listBuffer.length) {
      return;
    }
    blocks.push({
      key: `list-${blocks.length}`,
      type: "list",
      items: [...listBuffer],
    });
    listBuffer = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    if (line.startsWith("#")) {
      flushParagraph();
      flushList();
      const headingMatch = /^(#+)\s*(.*)$/.exec(line);
      if (headingMatch) {
        blocks.push({
          key: `heading-${blocks.length}`,
          type: "heading",
          level: headingMatch[1].length,
          text: headingMatch[2],
        });
      }
      continue;
    }

    if (line.startsWith("- ")) {
      flushParagraph();
      listBuffer.push(line.slice(2).trim());
      continue;
    }

    flushList();
    paragraphBuffer.push(line);
  }

  flushParagraph();
  flushList();
  return blocks;
}
