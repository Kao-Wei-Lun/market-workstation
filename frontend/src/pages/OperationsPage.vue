<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="管理"
      title="任務中心"
      description="手動觸發本機常用任務，並查看最近執行結果、資料新鮮度與系統健康狀態。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
          查看報表
        </RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'candidates', query: { candidateDate: selectedTradeDate || undefined } }">
          查看候選
        </RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'coverage' }">資料覆蓋</RouterLink>
      </div>
    </PageHeader>

    <FilterBar title="任務與狀態檢視" description="調整手動任務日期、近期工作筆數與 worker 過舊判定門檻。">
      <div class="form-inline">
        <div class="field-group">
          <label for="task-trade-date">任務日期</label>
          <input id="task-trade-date" v-model="selectedTradeDate" type="date" />
        </div>
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
          <button @click="loadPage">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="任務中心資料狀態"
      :as-of-date="status?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(status?.meta.generated_at)"
      :item-count="(status?.meta.item_count ?? 0) + (taskCenter?.meta.item_count ?? 0)"
      hint="此頁面整合手動任務、資料新鮮度、工作紀錄與 worker 心跳。"
      demo-hint="若畫面仍是空的，可先執行 make demo-data，或在此頁直接手動觸發示範資料、指標、候選與報表任務。"
      :show-refresh="true"
      @refresh="loadPage"
    />

    <LoadingState v-if="isLoading" message="正在載入任務中心與系統狀態..." />
    <ErrorState
      v-else-if="errorMessage"
      title="任務中心載入失敗"
      message="無法從後端取得手動任務、近期工作與健康狀態。"
      :detail="errorMessage"
    />
    <template v-else-if="status && taskCenter && coverage">
      <SummaryCardGrid :cards="taskSummaryCards" />

      <DetailPanel title="任務與營運重點" description="先檢查最近手動任務，再確認資料集、匯入工作與 worker 是否正常。">
        <ul class="highlights">
          <li v-for="item in combinedHighlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <DetailPanel title="手動觸發常用任務" description="這些操作都設計為本機單人開發與驗證用途，會同步回傳成功或錯誤結果。">
          <template #header>
            <div class="detail-actions">
              <span class="pill info">任務日期 {{ selectedTradeDate || "未指定" }}</span>
              <span class="pill">可執行 {{ taskCenter.data.available_actions.length }} 種任務</span>
            </div>
          </template>
          <div class="task-grid">
            <button
              v-for="action in taskCenter.data.available_actions"
              :key="action.action_key"
              class="task-button"
              :disabled="runningActionKey === action.action_key"
              @click="triggerTask(action.action_key)"
            >
              <strong>{{ action.label }}</strong>
              <span>{{ action.description }}</span>
              <small>結果頁：{{ action.target_label }}</small>
              <small v-if="action.suggested_trade_date">建議日期：{{ formatDate(action.suggested_trade_date) }}</small>
              <small v-if="runningActionKey === action.action_key">執行中...</small>
            </button>
          </div>
          <p
            v-if="actionFeedback"
            class="action-feedback"
            :class="{ 'action-feedback-error': Boolean(lastTaskResult && lastTaskResult.status === 'failed') || !lastTaskResult }"
          >
            {{ actionFeedback }}
          </p>
        </DetailPanel>

        <DetailPanel
          v-if="lastTaskResult"
          title="最近手動執行結果"
          :description="lastTaskResult.message"
        >
          <template #header>
            <div class="detail-actions">
              <span class="pill" :class="lastTaskResult.status === 'success' ? 'positive' : 'negative'">
                {{ lastTaskResult.status === "success" ? "成功" : "失敗" }}
              </span>
              <RouterLink
                v-if="lastTaskResult.target_route_name"
                class="detail-link"
                :to="taskTargetRoute"
              >
                前往結果頁
              </RouterLink>
            </div>
          </template>
          <MetricGrid :metrics="lastTaskMetrics" />
        </DetailPanel>

        <MetricGrid :metrics="systemMetrics" />
        <MetricGrid :metrics="coverageMetrics" />
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
          title="需補跑的 universe / scope"
          description="快速查看哪些區段尚未完成 bootstrap、缺資料或資料已過期。"
          :columns="coverageColumns"
          :rows="coverageRows"
          default-sort-by="attention_score"
          default-sort-direction="desc"
          empty-message="目前沒有需要補跑的 universe 區段。"
        />
        <SortableTableSection
          title="最近手動任務"
          description="查看本機手動觸發的示範資料、ETL、指標、候選與報表執行情況。"
          :columns="taskColumns"
          :rows="taskRows"
          default-sort-by="started_at"
          default-sort-direction="desc"
          empty-message="目前沒有手動任務紀錄，可先執行上方任務。"
        />
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
import { RouterLink } from "vue-router";
import { useRoute, useRouter } from "vue-router";

import { normalizeApiError } from "@/api/http";
import { fetchManualTaskCenter, fetchSystemStatus, fetchUniverseCoverage, runManualTask } from "@/api/system";
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
import type { ManualTaskCenterRead, ManualTaskRunRead, SystemStatusRead, UniverseCoverageRead } from "@/types/system";
import { formatDate, formatDateTime, formatList, formatNumber } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const status = ref<SystemStatusRead | null>(null);
const taskCenter = ref<ManualTaskCenterRead | null>(null);
const coverage = ref<UniverseCoverageRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const actionFeedback = ref<string | null>(null);
const runningActionKey = ref<string | null>(null);
const lastTaskResult = ref<ManualTaskRunRead | null>(null);
const jobLimit = ref(20);
const workerStaleMinutes = ref(30);
const selectedTradeDate = ref("");
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

const taskColumns = [
  { key: "label", label: "任務" },
  { key: "status", label: "狀態" },
  { key: "trade_date", label: "日期" },
  { key: "started_at", label: "開始時間" },
  { key: "finished_at", label: "完成時間" },
  { key: "target", label: "結果頁" },
  { key: "error", label: "錯誤摘要" },
];

const coverageColumns = [
  { key: "scope", label: "區段" },
  { key: "status", label: "狀態" },
  { key: "latest_data_date", label: "最新日期" },
  { key: "missing_data", label: "缺資料" },
  { key: "stale_data", label: "過期" },
  { key: "sample_symbols", label: "樣本代號" },
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

const taskRows = computed(() =>
  (taskCenter.value?.data.recent_tasks ?? []).map((task) => ({
    label: task.label,
    status: task.status === "success" ? "成功" : task.status === "failed" ? "失敗" : task.status,
    trade_date: formatDate(task.trade_date),
    started_at: formatDateTime(task.started_at),
    finished_at: formatDateTime(task.finished_at),
    target: actionRouteNameMap[task.action_key]
      ? makeLinkedCell(task.target_label, { name: actionRouteNameMap[task.action_key], query: task.trade_date ? taskQueryMap(task) : {} })
      : task.target_label,
    error: task.error_summary ?? "—",
  })),
);

const coverageRows = computed(() =>
  (coverage.value?.data.scopes ?? [])
    .filter((scope) => scope.status !== "ready")
    .map((scope) => ({
      scope: scope.label,
      status: scope.status === "stale" ? "資料過期" : scope.status === "partial" ? "部分完成" : "缺資料",
      latest_data_date: formatDate(scope.latest_data_date),
      missing_data: scope.missing_data_count,
      stale_data: scope.stale_data_count,
      attention_score: scope.missing_data_count * 10 + scope.stale_data_count,
      sample_symbols: formatList(
        scope.sample_missing_symbols.length > 0 ? scope.sample_missing_symbols : scope.sample_stale_symbols,
        "無",
      ),
    })),
);

const taskSummaryCards = computed(() => [...(taskCenter.value?.summary_cards ?? []), ...(status.value?.summary_cards ?? [])]);

const combinedHighlights = computed(() => [...(taskCenter.value?.highlights ?? []), ...(status.value?.highlights ?? [])]);

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

const coverageMetrics = computed(() => [
  {
    label: "已 bootstrap 區段",
    value: formatNumber(coverage.value?.data.completeness.bootstrapped_scope_count ?? 0),
    hint: `共 ${coverage.value?.data.completeness.scopes_declared ?? 0} 個 scope`,
  },
  {
    label: "就緒區段",
    value: formatNumber(coverage.value?.data.completeness.ready_scope_count ?? 0),
    hint: "沒有缺資料或過期",
  },
  {
    label: "需補跑區段",
    value: formatNumber(coverage.value?.data.completeness.attention_scope_count ?? 0),
    hint: "可先補 ETL 或 bootstrap",
  },
  {
    label: "有資料標的",
    value: formatNumber(coverage.value?.data.completeness.instruments_with_data_count ?? 0),
    hint: "含日線或序列資料",
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

const lastTaskMetrics = computed(() =>
  Object.entries(lastTaskResult.value?.metrics ?? {}).map(([key, value]) => ({
    label: taskMetricLabels[key] ?? key,
    value: formatNumber(value),
    hint: "本次執行結果",
  })),
);

const taskTargetRoute = computed(() => {
  const result = lastTaskResult.value;
  if (!result?.target_route_name) {
    return { name: "operations" as const };
  }
  return {
    name: result.target_route_name,
    query: result.trade_date ? taskResultQuery(result) : {},
  };
});

async function loadPage(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [taskPayload, statusPayload, coveragePayload] = await Promise.all([
      fetchManualTaskCenter({ limit: jobLimit.value }),
      fetchSystemStatus({
        jobLimit: jobLimit.value,
        workerStaleMinutes: workerStaleMinutes.value,
      }),
      fetchUniverseCoverage("v1_market_expanded"),
    ]);
    taskCenter.value = taskPayload;
    status.value = statusPayload;
    coverage.value = coveragePayload;
    await router.replace({
      query: {
        tradeDate: selectedTradeDate.value || undefined,
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

async function triggerTask(actionKey: string): Promise<void> {
  runningActionKey.value = actionKey;
  actionFeedback.value = null;
  try {
    lastTaskResult.value = await runManualTask(actionKey, {
      trade_date: selectedTradeDate.value || null,
    });
    actionFeedback.value = `${lastTaskResult.value.label}完成，可前往${lastTaskResult.value.target_label}查看結果。`;
    await loadPage();
  } catch (error) {
    const normalized = normalizeApiError(error);
    actionFeedback.value = `任務執行失敗：${normalized.detail}`;
  } finally {
    runningActionKey.value = null;
  }
}

onMounted(async () => {
  if (typeof route.query.tradeDate === "string") {
    selectedTradeDate.value = route.query.tradeDate;
  }
  if (typeof route.query.jobLimit === "string") {
    jobLimit.value = Number(route.query.jobLimit) || jobLimit.value;
  }
  if (typeof route.query.stale === "string") {
    workerStaleMinutes.value = Number(route.query.stale) || workerStaleMinutes.value;
  }
  await loadPage();
});

const actionRouteNameMap: Record<string, string> = {
  demo_data: "overview",
  sample_market_etl: "operations",
  indicator_update: "candidates",
  candidate_generation: "candidates",
  report_generation: "reports",
};

const taskMetricLabels: Record<string, string> = {
  daily_bars_loaded: "新增日線筆數",
  indicator_values_persisted: "寫入指標筆數",
  tw_derivatives_features_persisted: "衍生性商品特徵筆數",
  candidate_items_created: "候選筆數",
  candidate_runs_created: "候選批次",
  backtest_trades_created: "回測交易筆數",
  reports_persisted: "保存報表數",
  instruments_processed: "處理標的數",
};

function taskQueryMap(task: { action_key: string; trade_date: string | null }): Record<string, string> {
  if (!task.trade_date) {
    return {};
  }
  if (task.action_key === "candidate_generation" || task.action_key === "indicator_update") {
    return { candidateDate: task.trade_date };
  }
  if (task.action_key === "report_generation") {
    return { reportDate: task.trade_date };
  }
  return { tradeDate: task.trade_date };
}

function taskResultQuery(result: ManualTaskRunRead): Record<string, string> {
  if (!result.trade_date) {
    return {};
  }
  if (result.action_key === "candidate_generation" || result.action_key === "indicator_update") {
    return { candidateDate: result.trade_date };
  }
  if (result.action_key === "report_generation") {
    return { reportDate: result.trade_date };
  }
  if (result.action_key === "demo_data") {
    return { tradeDate: result.trade_date };
  }
  return { tradeDate: result.trade_date };
}
</script>

<style scoped>
.page-actions,
.detail-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.pill.link-pill,
.detail-link {
  text-decoration: none;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
}

.task-button {
  display: grid;
  gap: 0.35rem;
  align-items: start;
  text-align: left;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel-bg);
  padding: 1rem;
  cursor: pointer;
}

.task-button:disabled {
  opacity: 0.7;
  cursor: progress;
}

.task-button span,
.task-button small {
  color: var(--text-muted);
}

.action-feedback {
  margin-top: 0.75rem;
  color: var(--text-muted);
}

.action-feedback-error {
  color: #9f2d2d;
}
</style>
