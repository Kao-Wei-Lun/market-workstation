import { deleteJson, getJson, postJson } from "@/api/http";
import type {
  ChartAnnotationCreateRequest,
  ChartAnnotationRead,
  ChartDataRead,
  ChartInstrumentRead,
  InstitutionalFlowChartRead,
  MarketStructureChartRead,
} from "@/types/charts";

export async function fetchChartInstruments(params: {
  query?: string;
  market?: string;
  assetType?: string;
  limit?: number;
} = {}): Promise<ChartInstrumentRead[]> {
  return getJson<ChartInstrumentRead[]>("/api/charts/instruments", {
    params: {
      query: params.query,
      market: params.market,
      asset_type: params.assetType,
      limit: params.limit,
    },
  });
}

export async function fetchChartData(
  symbol: string,
  params: {
    dateFrom?: string;
    dateTo?: string;
    indicatorNames?: string[];
    viewKind?: "instrument" | "index" | "market_flow";
  } = {},
): Promise<ChartDataRead> {
  return getJson<ChartDataRead>(`/api/charts/ohlcv/${symbol}`, {
    params: {
      date_from: params.dateFrom,
      date_to: params.dateTo,
      indicator_name: params.indicatorNames,
      view_kind: params.viewKind,
    },
  });
}

export async function fetchInstitutionalFlowChart(
  symbol: string,
  params: { dateFrom?: string; dateTo?: string } = {},
): Promise<InstitutionalFlowChartRead> {
  return getJson<InstitutionalFlowChartRead>(`/api/charts/institutional-flow/${symbol}`, {
    params: {
      date_from: params.dateFrom,
      date_to: params.dateTo,
    },
  });
}

export async function fetchMarketStructureChart(
  symbol: string,
  params: { dateFrom?: string; dateTo?: string } = {},
): Promise<MarketStructureChartRead> {
  return getJson<MarketStructureChartRead>(`/api/charts/market-structure/${symbol}`, {
    params: {
      date_from: params.dateFrom,
      date_to: params.dateTo,
    },
  });
}

export async function createChartAnnotation(
  payload: ChartAnnotationCreateRequest,
): Promise<ChartAnnotationRead> {
  return postJson<ChartAnnotationRead, ChartAnnotationCreateRequest>("/api/charts/annotations", payload);
}

export async function fetchChartAnnotations(
  symbol: string,
  viewKind: "instrument" | "index" | "market_flow",
): Promise<ChartAnnotationRead[]> {
  return getJson<ChartAnnotationRead[]>(`/api/charts/annotations/${symbol}`, {
    params: { view_kind: viewKind },
  });
}

export async function clearChartAnnotations(
  symbol: string,
  viewKind: "instrument" | "index" | "market_flow",
): Promise<{ symbol: string; deleted: number }> {
  return deleteJson<{ symbol: string; deleted: number }>(`/api/charts/annotations/clear/${symbol}`, {
    params: { view_kind: viewKind },
  });
}

export async function deleteChartAnnotation(annotationId: number): Promise<void> {
  await deleteJson(`/api/charts/annotations/${annotationId}`);
}
