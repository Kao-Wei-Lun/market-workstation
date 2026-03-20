import { getJson } from "@/api/http";
import type { CandidateRunWithItemsRead } from "@/types/api";
import type { CandidateItemRead, CandidateRunRead } from "@/types/dashboard";

export async function fetchCandidateRuns(params: { candidateDate?: string; limit?: number } = {}): Promise<CandidateRunRead[]> {
  return getJson<CandidateRunRead[]>("/candidates/runs", {
    params: {
      candidate_date: params.candidateDate,
      limit: params.limit,
    },
  });
}

export async function fetchCandidateRunItems(runId: number): Promise<CandidateItemRead[]> {
  return getJson<CandidateItemRead[]>(`/candidates/runs/${runId}/items`);
}

export async function fetchLatestCandidateSummary(candidateDate?: string): Promise<CandidateRunWithItemsRead> {
  return getJson<CandidateRunWithItemsRead>("/candidates/summary/latest", {
    params: { candidate_date: candidateDate },
  });
}
