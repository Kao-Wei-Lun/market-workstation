import { getJson } from "@/api/http";
import type { DailyInstitutionalBiasSummary } from "@/types/dashboard";

export async function fetchLatestDerivativesSummary(): Promise<DailyInstitutionalBiasSummary> {
  return getJson<DailyInstitutionalBiasSummary>("/derivatives/summary/latest");
}
