import type {
  ChartAnnotationRead,
  ChartCandleRead,
  ChartIndicatorSeriesRead,
  InstitutionalFlowPointRead,
} from "@/types/charts";

export type ChartDrawingTool = "none" | "trend_line" | "horizontal_line" | "vertical_line" | "range_box" | "point_marker";

export interface ChartPlotClickPayload {
  tradeDate: string;
  price: number;
}

export interface ChartOverlayLine {
  key: string;
  label: string;
  color: string;
  points: { tradeDate: string; value: number }[];
}

const OVERLAY_COLORS = ["#165992", "#cf7c00", "#1b7f5a", "#9a3d7a", "#7b5ce1", "#555f6b"];

export function parseNumeric(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function buildOverlayLines(indicators: ChartIndicatorSeriesRead[]): ChartOverlayLine[] {
  return indicators.map((series, index) => ({
    key: `${series.indicator_name}:${series.component}:${series.parameter_signature}`,
    label: `${series.indicator_name.toUpperCase()} ${series.component}`,
    color: OVERLAY_COLORS[index % OVERLAY_COLORS.length],
    points: series.points
      .map((point) => ({
        tradeDate: point.trade_date,
        value: parseNumeric(point.value) ?? 0,
      }))
      .filter((point) => Number.isFinite(point.value)),
  }));
}

export function latestCandle(candles: ChartCandleRead[]): ChartCandleRead | null {
  return candles.length ? candles[candles.length - 1] : null;
}

export function buildDateRange(latestDate: string | null | undefined, days: number): { dateFrom: string; dateTo: string } {
  const base = latestDate ? new Date(`${latestDate}T00:00:00`) : new Date();
  const start = new Date(base);
  start.setDate(base.getDate() - days);
  return {
    dateFrom: toLocalDateInput(start),
    dateTo: toLocalDateInput(base),
  };
}

export function describeAnnotation(annotation: ChartAnnotationRead): string {
  if (annotation.annotation_type === "vertical_line") {
    return `垂直線 ${annotation.label ?? ""}`.trim();
  }
  if (annotation.annotation_type === "range_box") {
    return `區間框 ${annotation.label ?? ""}`.trim();
  }
  if (annotation.annotation_type === "point_marker") {
    return `重點標記 ${annotation.label ?? ""}`.trim();
  }
  if (annotation.annotation_type === "horizontal_line") {
    return `水平線 ${annotation.label ?? ""}`.trim();
  }
  return `趨勢線 ${annotation.label ?? ""}`.trim();
}

export function chartToolLabel(tool: ChartDrawingTool): string {
  switch (tool) {
    case "trend_line":
      return "趨勢線";
    case "horizontal_line":
      return "水平線";
    case "vertical_line":
      return "垂直線";
    case "range_box":
      return "區間框";
    case "point_marker":
      return "重點標記";
    default:
      return "未啟用";
  }
}

export function formatFlowHighlight(point: InstitutionalFlowPointRead | null): string {
  if (!point) {
    return "目前沒有法人流向資料。";
  }
  return `期貨淨未平倉 ${point.futures_net_open_interest}、選擇權淨未平倉 ${point.options_net_open_interest}`;
}

function toLocalDateInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
