import { getJson } from "@/api/http";
import type { CandidateItemApiRead, CandidateRunWithItemsRead } from "@/types/api";
import type { CandidateItemRead, CandidateRunRead } from "@/types/dashboard";

export function normalizeCandidateItem(item: CandidateItemApiRead): CandidateItemRead {
  return {
    ...item,
    candidate_reasons: item.candidate_reasons ?? item.candidate_reasons_json ?? [],
    supporting_metrics: item.supporting_metrics ?? item.supporting_metrics_json ?? {},
  };
}

export async function fetchCandidateRuns(params: { candidateDate?: string; limit?: number } = {}): Promise<CandidateRunRead[]> {
  return getJson<CandidateRunRead[]>("/candidates/runs", {
    params: {
      candidate_date: params.candidateDate,
      limit: params.limit,
    },
  });
}

export async function fetchCandidateRunItems(runId: number): Promise<CandidateItemRead[]> {
  const items = await getJson<CandidateItemApiRead[]>(`/candidates/runs/${runId}/items`);
  return items.map(normalizeCandidateItem);
}

export async function fetchLatestCandidateSummary(candidateDate?: string): Promise<CandidateRunWithItemsRead> {
  const response = await getJson<{ run: CandidateRunRead; items: CandidateItemApiRead[] }>("/candidates/summary/latest", {
    params: { candidate_date: candidateDate },
  });
  return {
    run: response.run,
    items: (response.items ?? []).map(normalizeCandidateItem),
  };
}
