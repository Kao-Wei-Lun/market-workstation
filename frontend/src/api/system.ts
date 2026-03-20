import { getJson, postJson } from "@/api/http";
import type {
  ManualTaskCenterRead,
  ManualTaskRunRead,
  SystemStatusRead,
  UniverseCoverageRead,
} from "@/types/system";

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

export async function fetchManualTaskCenter(params: { limit?: number } = {}): Promise<ManualTaskCenterRead> {
  return getJson<ManualTaskCenterRead>("/api/system/tasks", {
    params: {
      limit: params.limit,
    },
  });
}

export async function runManualTask(
  actionKey: string,
  payload: { trade_date?: string | null } = {},
): Promise<ManualTaskRunRead> {
  return postJson<ManualTaskRunRead, { trade_date?: string | null }>(`/api/system/tasks/${actionKey}`, payload);
}
