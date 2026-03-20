import { getJson } from "@/api/http";
import type { BacktestRunRead, BacktestTradeRead } from "@/types/dashboard";

export async function fetchBacktestRuns(limit = 20): Promise<BacktestRunRead[]> {
  return getJson<BacktestRunRead[]>("/backtests/runs", {
    params: { limit },
  });
}

export async function fetchBacktestRunTrades(runId: number): Promise<BacktestTradeRead[]> {
  return getJson<BacktestTradeRead[]>(`/backtests/runs/${runId}/trades`);
}
