export type SortDirection = "asc" | "desc";
export type TableRow = Record<string, unknown>;

function normalizeValue(value: unknown): string | number {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "number") {
    return value;
  }
  const stringValue = String(value);
  const parsedNumber = Number(stringValue.replace(/,/g, "").replace("%", ""));
  if (!Number.isNaN(parsedNumber) && stringValue.trim() !== "") {
    return parsedNumber;
  }
  return stringValue.toLowerCase();
}

export function sortRows<T extends TableRow>(
  rows: T[],
  sortBy: string,
  direction: SortDirection = "asc",
): T[] {
  const factor = direction === "asc" ? 1 : -1;
  return [...rows].sort((left, right) => {
    const leftValue = normalizeValue(left[sortBy]);
    const rightValue = normalizeValue(right[sortBy]);
    if (leftValue < rightValue) {
      return -1 * factor;
    }
    if (leftValue > rightValue) {
      return 1 * factor;
    }
    return 0;
  });
}

export function filterRowsByQuery<T extends TableRow>(
  rows: T[],
  keys: string[],
  query: string,
): T[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return rows;
  }
  return rows.filter((row) =>
    keys.some((key) => {
      const value = row[key];
      if (value === null || value === undefined) {
        return false;
      }
      return String(value).toLowerCase().includes(normalizedQuery);
    }),
  );
}

export interface ChartPointInput {
  label: string;
  value: number;
  tone?: "positive" | "negative" | "neutral" | "info";
}

export interface ChartPoint extends ChartPointInput {
  percentage: number;
}

export function buildChartPoints(points: ChartPointInput[]): ChartPoint[] {
  const maxValue = Math.max(...points.map((point) => Math.abs(point.value)), 0);
  if (maxValue === 0) {
    return points.map((point) => ({ ...point, percentage: 0 }));
  }
  return points.map((point) => ({
    ...point,
    percentage: Math.round((Math.abs(point.value) / maxValue) * 100),
  }));
}
