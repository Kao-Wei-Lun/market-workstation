<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="管理"
      title="系統狀態"
      description="檢查最近資料更新、匯入工作、worker 心跳與本機系統健康狀態。"
    />

    <FilterBar title="作業檢視" description="調整近期工作筆數與 worker 過舊判定門檻。">
      <div class="form-inline">
        <div class="field-group">
          <label for="job-limit">最近工作筆數</label>
          <input id="job-limit" v-model.number="jobLimit" type="number" min="5" max="100" step="5" />
        </div>
        <div class="field-group">
          <label for="stale-minutes">過舊分鐘數</label>
          <input id="stale-minutes" v-model.number="workerStaleMinutes" type="number" min="5" max="1440" step="5" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadStatus">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="系統資料狀態"
      :as-of-date="status?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(status?.meta.generated_at)"
      :item-count="status?.meta.item_count"
      hint="此頁面整合資料新鮮度、工作紀錄與 worker 心跳。"
      demo-hint="若工作紀錄為空，可先執行 make demo-data 或手動跑 sample-etl / generate-reports。"
      :show-refresh="true"
      @refresh="loadStatus"
    />

    <LoadingState v-if="isLoading" message="正在載入系統狀態..." />
    <ErrorState
      v-else-if="errorMessage"
      title="系統狀態載入失敗"
      message="無法從後端取得近期工作與健康狀態。"
      :detail="errorMessage"
    />
    <template v-else-if="status">
      <SummaryCardGrid :cards="status.summary_cards" />

      <DetailPanel title="營運重點" description="快速檢查最近工作、資料集與 worker 是否正常。">
        <ul class="highlights">
          <li v-for="item in status.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <MetricGrid :metrics="systemMetrics" />
        <MiniBarChart
          title="資料集新鮮度"
          description="顯示主要資料集目前可用筆數。"
          :points="datasetChartPoints"
          empty-message="目前沒有資料集資訊。"
        />
        <MiniBarChart
          title="工作狀態統計"
          description="顯示匯入工作的狀態分布。"
          :points="jobStatusChartPoints"
          empty-message="目前沒有工作狀態統計。"
        />
      </div>

      <div class="page-section-grid">
        <SortableTableSection
          title="最近資料更新"
          description="檢查主要資料集最後更新日期與目前總筆數。"
          :columns="datasetColumns"
          :rows="datasetRows"
          default-sort-by="latest_date"
          default-sort-direction="desc"
          empty-message="目前沒有資料集更新資訊。"
        />
        <SortableTableSection
          title="最近 ETL / Ingest Jobs"
          description="查看近期排程或手動執行的匯入工作狀態。"
          :columns="jobColumns"
          :rows="jobRows"
          default-sort-by="started_at"
          default-sort-direction="desc"
          empty-message="目前沒有匯入工作紀錄。"
        />
        <SortableTableSection
          title="Worker 心跳"
          description="檢查 scheduler / analysis 等 worker 是否持續回報心跳。"
          :columns="workerColumns"
          :rows="workerRows"
          default-sort-by="heartbeat_at"
          default-sort-direction="desc"
          empty-message="目前沒有 worker 心跳紀錄。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { normalizeApiError } from "@/api/http";
import { fetchSystemStatus } from "@/api/system";
import DetailPanel from "@/components/DetailPanel.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageHeader from "@/components/PageHeader.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { SystemStatusRead } from "@/types/system";
import { formatDate, formatDateTime, formatNumber } from "@/utils/formatters";

const status = ref<SystemStatusRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const jobLimit = ref(20);
const workerStaleMinutes = ref(30);
const route = useRoute();
const router = useRouter();

const datasetColumns = [
  { key: "label", label: "資料集" },
  { key: "latest_date", label: "最新日期" },
  { key: "record_count", label: "筆數" },
  { key: "status", label: "狀態" },
];

const jobColumns = [
  { key: "job_type", label: "工作類型" },
  { key: "source_route", label: "資料來源" },
  { key: "status", label: "狀態" },
  { key: "trade_date", label: "交易日期" },
  { key: "started_at", label: "開始時間" },
];

const workerColumns = [
  { key: "worker_name", label: "Worker" },
  { key: "worker_role", label: "角色" },
  { key: "status", label: "狀態" },
  { key: "heartbeat_at", label: "心跳時間" },
  { key: "last_job", label: "最近工作" },
];

const datasetRows = computed(() =>
  (status.value?.data.datasets ?? []).map((dataset) => ({
    label: dataset.label,
    latest_date: formatDate(dataset.latest_date),
    record_count: dataset.record_count,
    status: dataset.status === "ready" ? "就緒" : "缺資料",
  })),
);

const jobRows = computed(() =>
  (status.value?.data.recent_jobs ?? []).map((job) => ({
    job_type: job.job_type,
    source_route: job.source_route,
    status: job.status,
    trade_date: formatDate(job.trade_date),
    started_at: formatDateTime(job.started_at),
  })),
);

const workerRows = computed(() =>
  (status.value?.data.workers ?? []).map((worker) => ({
    worker_name: worker.worker_name,
    worker_role: worker.worker_role,
    status: worker.stale ? "過舊" : worker.status,
    heartbeat_at: formatDateTime(worker.heartbeat_at),
    last_job: worker.last_job_name ?? "無",
  })),
);

const systemMetrics = computed(() => [
  { label: "資料集", value: formatNumber(status.value?.data.datasets.length ?? 0), hint: "主要資料表" },
  { label: "近期工作", value: formatNumber(status.value?.data.recent_jobs.length ?? 0), hint: "依目前查詢上限" },
  {
    label: "活躍 Worker",
    value: formatNumber((status.value?.data.workers ?? []).filter((worker) => !worker.stale).length),
    hint: "心跳未過舊",
  },
  {
    label: "失敗工作",
    value: formatNumber(
      status.value?.data.job_status_counts.find((item) => item.status === "failed")?.count ?? 0,
    ),
    hint: "僅統計 ingest_jobs",
  },
]);

const datasetChartPoints = computed(() =>
  (status.value?.data.datasets ?? []).map((dataset) => ({
    label: dataset.label,
    value: dataset.record_count,
    tone: dataset.status === "ready" ? ("positive" as const) : ("negative" as const),
  })),
);

const jobStatusChartPoints = computed(() =>
  (status.value?.data.job_status_counts ?? []).map((item) => ({
    label: item.status,
    value: item.count,
    tone: item.status === "failed" ? ("negative" as const) : ("info" as const),
  })),
);

async function loadStatus(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    status.value = await fetchSystemStatus({
      jobLimit: jobLimit.value,
      workerStaleMinutes: workerStaleMinutes.value,
    });
    await router.replace({
      query: {
        jobLimit: String(jobLimit.value),
        stale: String(workerStaleMinutes.value),
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  if (typeof route.query.jobLimit === "string") {
    jobLimit.value = Number(route.query.jobLimit) || jobLimit.value;
  }
  if (typeof route.query.stale === "string") {
    workerStaleMinutes.value = Number(route.query.stale) || workerStaleMinutes.value;
  }
  await loadStatus();
});
</script>
