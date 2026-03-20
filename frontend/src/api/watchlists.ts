import { getJson } from "@/api/http";
import type { WatchlistItemRead } from "@/types/api";
import type { GroupSummaryRead, WatchlistRead } from "@/types/dashboard";

export async function fetchWatchlists(): Promise<WatchlistRead[]> {
  return getJson<WatchlistRead[]>("/watchlists");
}

export async function fetchWatchlistItems(watchlistId: number): Promise<WatchlistItemRead[]> {
  return getJson<WatchlistItemRead[]>(`/watchlists/${watchlistId}/items`);
}

export async function fetchWatchlistSummary(watchlistId: number, tradeDate: string): Promise<GroupSummaryRead> {
  return getJson<GroupSummaryRead>(`/watchlists/${watchlistId}/summary`, {
    params: { trade_date: tradeDate },
  });
}
