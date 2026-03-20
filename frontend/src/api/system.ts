import { getJson } from "@/api/http";
import type { SystemStatusRead, UniverseCoverageRead } from "@/types/system";

export async function fetchUniverseCoverage(presetName?: string): Promise<UniverseCoverageRead> {
  return getJson<UniverseCoverageRead>("/api/system/coverage", {
    params: { preset_name: presetName },
  });
}

export async function fetchSystemStatus(params: {
  jobLimit?: number;
  workerStaleMinutes?: number;
} = {}): Promise<SystemStatusRead> {
  return getJson<SystemStatusRead>("/api/system/status", {
    params: {
      job_limit: params.jobLimit,
      worker_stale_minutes: params.workerStaleMinutes,
    },
  });
}
