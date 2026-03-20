<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="候選清單"
      description="查看隔日觀察候選名單、排序分數與掃描脈絡。"
    />

    <FilterBar
      title="候選探索"
      description="直接在頁面內篩選與排序候選名單。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="candidate-date">候選日期</label>
          <input id="candidate-date" v-model="candidateDate" type="date" />
        </div>
        <div class="field-group">
          <label for="candidate-limit">筆數</label>
          <select id="candidate-limit" v-model="limit" @change="loadCandidates">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </div>
        <div class="field-group">
          <label for="candidate-run">批次</label>
          <select id="candidate-run" v-model="selectedRunIdString" @change="loadSelectedRunItems">
            <option value="">最新批次</option>
            <option v-for="run in runs" :key="run.id" :value="String(run.id)">
              #{{ run.id }} {{ formatDate(run.candidate_date) }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="candidate-query">搜尋</label>
          <input id="candidate-query" v-model="searchQuery" placeholder="代號或原因" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadCandidates">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="候選資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="候選批次整合排序分數、理由清單與掃描脈絡。"
      demo-hint="若尚無候選資料，請執行 make demo-data 產生示範批次。"
      :show-refresh="true"
      @refresh="loadCandidates"
    />

    <LoadingState v-if="isLoading" message="正在載入候選清單..." />
    <ErrorState
      v-else-if="errorMessage"
      title="候選資料載入失敗"
      message="無法載入最新候選批次資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無候選資料"
      message="後端目前還沒有候選批次。執行 make demo-data 後即可產生可重複的本機候選名單。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="目前候選批次" description="顯示目前批次摘要與衍生性商品脈絡。">
          <MetricGrid :metrics="candidateMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="候選分數排序"
          description="快速查看目前候選名單的分數強弱。"
          :points="candidateChartPoints"
          empty-message="目前沒有候選分數資料。"
        />
      </div>

      <DetailPanel title="候選脈絡" description="整理最新候選批次的重要觀察。">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="近期候選批次"
          description="顯示可在此頁面切換檢視的近期候選批次。"
          :columns="runColumns"
          :rows="runRows"
          row-key="run_key"
          :selected-row-key="selectedRunRowKey"
          :interactive-rows="true"
          @row-select="handleRunRowSelect"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="目前沒有候選批次。"
        />
        <SortableTableSection
          title="目前批次項目"
          description="顯示所選批次的候選名單與排序。"
          :columns="itemColumns"
          :rows="filteredItemRows"
          row-key="item_key"
          :selected-row-key="selectedItemRowKey"
          :interactive-rows="true"
          @row-select="handleItemRowSelect"
          default-sort-by="score"
          default-sort-direction="desc"
          empty-message="目前沒有候選項目。"
        />
      </div>

      <DetailPanel
        v-if="selectedCandidateItem"
        title="候選明細"
        description="顯示目前候選標的的理由與支援指標。"
      >
        <MetricGrid :metrics="selectedCandidateMetrics" />
      </DetailPanel>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchCandidateRunItems, fetchCandidateRuns } from "@/api/candidates";
import { fetchCandidatesDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { CandidateItemRead, CandidateRunRead, CandidatesDashboardRead } from "@/types/dashboard";
import { formatDate, formatDateTime, formatList, formatNumber } from "@/utils/formatters";
import type { TableRow } from "@/utils/presentation";
import { filterRowsByQuery } from "@/utils/presentation";

const dashboard = ref<CandidatesDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const searchQuery = ref("");
const candidateDate = ref("");
const runs = ref<CandidateRunRead[]>([]);
const items = ref<CandidateItemRead[]>([]);
const selectedRunId = ref<number | null>(null);
const selectedItemId = ref<number | null>(null);
const route = useRoute();
const router = useRouter();
const selectedRunIdString = computed({
  get: () => (selectedRunId.value ? String(selectedRunId.value) : ""),
  set: (value: string) => {
    selectedRunId.value = value ? Number(value) : null;
  },
});

const selectedRun = computed(() => runs.value.find((run) => run.id === selectedRunId.value) ?? null);
const selectedCandidateItem = computed(() => items.value.find((item) => item.id === selectedItemId.value) ?? null);
const selectedRunSummaryJson = computed<Record<string, unknown>>(
  () => (selectedRun.value?.summary_json as Record<string, unknown> | undefined) ?? {},
);

function summaryNumber(value: unknown): string {
  return formatNumber(typeof value === "string" || typeof value === "number" ? value : null);
}

const runColumns = [
  { key: "run_id", label: "批次" },
  { key: "date", label: "日期" },
  { key: "status", label: "狀態" },
  { key: "candidates", label: "候選數" },
];

const itemColumns = [
  { key: "rank", label: "排名" },
  { key: "symbol", label: "代號" },
  { key: "score", label: "分數" },
  { key: "reasons", label: "原因" },
];

const runRows = computed(() =>
  runs.value.map((run) => ({
    run_key: run.id,
    run_id: `#${run.id}${run.id === selectedRunId.value ? "（目前）" : ""}`,
    date: formatDate(run.candidate_date),
    status: run.status,
    candidates: run.total_candidates,
  })),
);

const itemRows = computed(() =>
  items.value.map((item) => ({
    item_key: item.id,
    rank: item.rank,
    symbol: item.symbol,
    score: Number(item.score),
    reasons: formatList(item.candidate_reasons, "無理由說明"),
  })),
);

const filteredItemRows = computed(() => filterRowsByQuery(itemRows.value, ["symbol", "reasons"], searchQuery.value));
const selectedRunRowKey = computed(() => (selectedRunId.value ? String(selectedRunId.value) : null));
const selectedItemRowKey = computed(() => (selectedItemId.value ? String(selectedItemId.value) : null));

const candidateMetrics = computed(() => {
  if (!selectedRun.value) {
    return [];
  }
  return [
    {
      label: "候選數",
      value: formatNumber(selectedRun.value.total_candidates),
      hint: "該日期已保存",
    },
    {
      label: "衍生性商品狀態",
      value: String(selectedRunSummaryJson.value.overall_derivatives_regime ?? "無資料"),
      hint: "市場脈絡",
    },
    {
      label: "偏向分數",
      value: summaryNumber(selectedRunSummaryJson.value.overall_derivatives_bias_score),
      hint: "摘要分數",
    },
    {
      label: "評估母體",
      value: summaryNumber(selectedRunSummaryJson.value.instruments_considered),
      hint: "參與評分標的",
    },
  ];
});

const candidateChartPoints = computed(() =>
  filteredItemRows.value.slice(0, 8).map((item) => ({
    label: String(item.symbol),
    value: Number(item.score),
    tone: "info" as const,
  })),
);

const selectedCandidateMetrics = computed(() => {
  if (!selectedCandidateItem.value) {
    return [];
  }
  return [
    { label: "代號", value: selectedCandidateItem.value.symbol, hint: "目前候選標的" },
    { label: "分數", value: formatNumber(selectedCandidateItem.value.score), hint: "整體排序分數" },
    { label: "原因", value: formatList(selectedCandidateItem.value.candidate_reasons, "無理由說明"), hint: "訊號摘要" },
    {
      label: "支援指標",
      value: JSON.stringify(selectedCandidateItem.value.supporting_metrics),
      hint: "原始支援內容",
    },
  ];
});

function handleRunRowSelect(row: TableRow): void {
  selectedRunId.value = Number(row.run_key);
  void loadSelectedRunItems();
}

function handleItemRowSelect(row: TableRow): void {
  selectedItemId.value = Number(row.item_key);
}

async function loadCandidates(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [dashboardResponse, runsResponse] = await Promise.all([
      fetchCandidatesDashboard({ candidateDate: candidateDate.value || undefined, limit: limit.value }),
      fetchCandidateRuns({ candidateDate: candidateDate.value || undefined, limit: limit.value }),
    ]);
    dashboard.value = dashboardResponse;
    runs.value = runsResponse;
    selectedRunId.value = selectedRunId.value ?? dashboardResponse.data?.run.id ?? runsResponse[0]?.id ?? null;
    await loadSelectedRunItems();
    await router.replace({
      query: {
        candidateDate: candidateDate.value || undefined,
        limit: String(limit.value),
        run: selectedRunId.value ? String(selectedRunId.value) : undefined,
        search: searchQuery.value || undefined,
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedRunItems(): Promise<void> {
  items.value = selectedRunId.value ? await fetchCandidateRunItems(selectedRunId.value) : [];
  selectedItemId.value = items.value[0]?.id ?? null;
}

onMounted(() => {
  candidateDate.value = typeof route.query.candidateDate === "string" ? route.query.candidateDate : "";
  searchQuery.value = typeof route.query.search === "string" ? route.query.search : "";
  limit.value = typeof route.query.limit === "string" ? Number(route.query.limit) : 10;
  selectedRunId.value = typeof route.query.run === "string" ? Number(route.query.run) : null;
  return loadCandidates();
});
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.5rem;
}
</style>
