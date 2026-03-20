export function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return String(value);
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(numberValue);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }
  return value.slice(0, 10);
}

export function formatPercent(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return String(value);
  }
  return `${numberValue.toFixed(2)}%`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }
  return value.replace("T", " ").slice(0, 16);
}

export function formatTitle(input: string): string {
  return input
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
