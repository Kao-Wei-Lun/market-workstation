export interface ChartInstrumentRead {
  id: number;
  symbol: string;
  name: string;
  market: string;
  asset_type: string;
  currency: string;
  timezone: string;
  source_route: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  latest_data_date: string | null;
}

export interface ChartCandleRead {
  trade_date: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
  change_percent: string | null;
}

export interface ChartIndicatorPointRead {
  trade_date: string;
  value: string;
}

export interface ChartIndicatorSeriesRead {
  indicator_name: string;
  component: string;
  parameter_signature: string;
  points: ChartIndicatorPointRead[];
}

export interface ChartAnnotationRead {
  id: number;
  instrument_id: number;
  symbol_snapshot: string;
  view_kind: "instrument" | "index" | "market_flow";
  annotation_type: "trend_line" | "horizontal_line" | "vertical_line" | "range_box" | "point_marker";
  timeframe: string;
  label: string | null;
  payload_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ChartDataRead {
  instrument: ChartInstrumentRead;
  candles: ChartCandleRead[];
  indicators: ChartIndicatorSeriesRead[];
  annotations: ChartAnnotationRead[];
  available_indicator_keys: string[];
}

export interface ChartAnnotationCreateRequest {
  symbol: string;
  view_kind: "instrument" | "index" | "market_flow";
  annotation_type: "trend_line" | "horizontal_line" | "vertical_line" | "range_box" | "point_marker";
  timeframe?: string;
  label?: string | null;
  payload_json: Record<string, unknown>;
}

export interface InstitutionalFlowPointRead {
  trade_date: string;
  spot_net_amount: string | null;
  futures_net_open_interest: number;
  futures_net_amount: string | null;
  options_net_open_interest: number;
  options_net_amount: string | null;
  options_directional_bias: string | null;
  average_bias_score: string | null;
  bullish_count: number;
  bearish_count: number;
  anomaly_count: number;
}

export interface InstitutionalFlowChartRead {
  instrument: ChartInstrumentRead;
  candles: ChartCandleRead[];
  flow_points: InstitutionalFlowPointRead[];
  spot_flow_available: boolean;
  summary_highlights: string[];
}

export interface MarketStructureSummaryRead {
  trade_date: string | null;
  overall_regime: string;
  spot_direction: string;
  futures_direction: string;
  options_direction: string;
  divergence_hints: string[];
  anomaly_hints: string[];
  highlights: string[];
}

export interface MarketStructureChartRead {
  instrument: ChartInstrumentRead;
  candles: ChartCandleRead[];
  flow_points: InstitutionalFlowPointRead[];
  available_series: string[];
  summary: MarketStructureSummaryRead;
}
