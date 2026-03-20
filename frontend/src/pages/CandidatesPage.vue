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
          <input id="candidate-query" v-model="searchQuery" placeholder="代號、理由、標籤" />
        </div>
        <div class="field-group">
          <label for="candidate-sort">排序</label>
          <select id="candidate-sort" v-model="candidateSortBy">
            <option value="score">依分數</option>
            <option value="rank">依名次</option>
            <option value="symbol">依代號</option>
            <option value="date">依日期</option>
          </select>
        </div>
        <div class="field-group">
          <label for="candidate-sort-direction">方向</label>
          <select id="candidate-sort-direction" v-model="candidateSortDirection">
            <option value="desc">由高到低</option>
            <option value="asc">由低到高</option>
          </select>
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
          :key="`${candidateSortBy}-${candidateSortDirection}`"
          title="目前批次項目"
          description="顯示所選批次的候選名單，可依分數、名次與代號篩選。"
          :columns="itemColumns"
          :rows="filteredItemRows"
          row-key="item_key"
          :selected-row-key="selectedItemRowKey"
          :interactive-rows="true"
          @row-select="handleItemRowSelect"
          :default-sort-by="candidateSortBy"
          :default-sort-direction="candidateSortDirection"
          empty-message="目前沒有候選項目。"
        />
      </div>

      <DetailPanel
        v-if="selectedCandidateItem"
        title="候選明細"
        description="顯示候選理由、分數拆解、群組脈絡與支援指標。"
      >
        <template #header>
          <div class="detail-actions">
            <RouterLink class="detail-link" :to="candidateReportLink">查看同日報表</RouterLink>
            <RouterLink v-if="candidateGroupLink" class="detail-link" :to="candidateGroupLink">查看相關群組</RouterLink>
            <RouterLink v-if="candidateWatchlistsLink" class="detail-link" :to="candidateWatchlistsLink">
              查看觀察清單
            </RouterLink>
          </div>
        </template>

        <div class="page-section-grid detail-grid">
          <DetailPanel title="候選摘要" description="快速檢查目前標的的排名、日期與關聯數量。">
            <MetricGrid :metrics="selectedCandidateOverviewMetrics" />
          </DetailPanel>
          <DetailPanel title="分數拆解" description="檢視技術分、動能分與脈絡加減分。">
            <MetricGrid :metrics="selectedCandidateScoreMetrics" />
          </DetailPanel>
        </div>

        <div class="page-section-grid detail-grid">
          <DetailPanel title="候選理由" description="整理排序理由，方便日常快速複核。">
            <ul class="detail-list">
              <li v-for="reason in selectedCandidateReasons" :key="reason">{{ reason }}</li>
            </ul>
          </DetailPanel>
          <DetailPanel title="關聯脈絡" description="彙整 tag、watchlist 與 scanner 參考資訊。">
            <MetricGrid :metrics="selectedCandidateContextMetrics" />
            <div class="chip-group">
              <span v-for="tagName in selectedCandidateTags" :key="`tag-${tagName}`" class="pill info">
                標籤 {{ tagName }}
              </span>
              <span
                v-for="watchlistName in selectedCandidateWatchlists"
                :key="`watchlist-${watchlistName}`"
                class="pill"
              >
                清單 {{ watchlistName }}
              </span>
            </div>
          </DetailPanel>
        </div>

        <SortableTableSection
          v-if="selectedCandidateScannerRows.length"
          title="掃描關聯"
          description="顯示該標的落在哪些群組或觀察清單，及是否命中 scanner。"
          :columns="scannerColumns"
          :rows="selectedCandidateScannerRows"
          row-key="scanner_key"
          default-sort-by="flagged"
          default-sort-direction="desc"
          empty-message="目前沒有掃描關聯。"
        />

        <StructuredPayloadSection
          title="支援指標原始內容"
          description="保留原始 supporting metrics，方便交叉比對與除錯。"
          :payload="selectedCandidateItem.supporting_metrics"
          empty-message="目前沒有支援指標內容。"
        />
      </DetailPanel>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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
import StructuredPayloadSection from "@/components/StructuredPayloadSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { CandidateItemRead, CandidateRunRead, CandidatesDashboardRead } from "@/types/dashboard";
import { formatDate, formatDateTime, formatList, formatNumber } from "@/utils/formatters";
import { buildCandidateDetailView } from "@/utils/candidates";
import type { SortDirection, TableRow } from "@/utils/presentation";
import { filterRowsByQuery, isLinkedCellValue, makeLinkedCell } from "@/utils/presentation";

const dashboard = ref<CandidatesDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const searchQuery = ref("");
const candidateSortBy = ref("score");
const candidateSortDirection = ref<SortDirection>("desc");
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
  { key: "contexts", label: "關聯" },
];

const scannerColumns = [
  { key: "name", label: "來源" },
  { key: "kind", label: "類型" },
  { key: "flagged", label: "命中" },
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
  items.value.map((item) => {
    const detail = buildCandidateDetailView(item);
    return {
      item_key: item.id,
      rank: item.rank,
      symbol: makeLinkedCell(item.symbol, {
        name: "reports",
        query: {
          reportDate: item.candidate_date,
        },
      }),
      score: Number(item.score),
      reasons: formatList(item.candidate_reasons, "無理由說明"),
      contexts: formatList(
        [...detail.tags, ...detail.watchlists, ...detail.scannerMemberships.map((membership) => membership.name)],
        "一般觀察",
      ),
      date: item.candidate_date,
    };
  }),
);

const filteredItemRows = computed(() =>
  filterRowsByQuery(itemRows.value, ["symbol", "reasons", "contexts"], searchQuery.value),
);
const selectedRunRowKey = computed(() => (selectedRunId.value ? String(selectedRunId.value) : null));
const selectedItemRowKey = computed(() => (selectedItemId.value ? String(selectedItemId.value) : null));
const selectedCandidateDetail = computed(() =>
  selectedCandidateItem.value ? buildCandidateDetailView(selectedCandidateItem.value) : null,
);

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
    label: isLinkedCellValue(item.symbol) ? item.symbol.label : String(item.symbol),
    value: Number(item.score),
    tone: "info" as const,
  })),
);

const selectedCandidateOverviewMetrics = computed(() => {
  if (!selectedCandidateItem.value) {
    return [];
  }
  return [
    { label: "代號", value: selectedCandidateItem.value.symbol, hint: "目前候選標的" },
    { label: "候選日期", value: formatDate(selectedCandidateItem.value.candidate_date), hint: "批次日期" },
    { label: "名次", value: formatNumber(selectedCandidateItem.value.rank), hint: "同批次排序" },
    { label: "總分", value: formatNumber(selectedCandidateItem.value.score), hint: "整體排序分數" },
  ];
});

const selectedCandidateScoreMetrics = computed(() => {
  if (!selectedCandidateDetail.value) {
    return [];
  }
  return selectedCandidateDetail.value.scoreBreakdown;
});

const selectedCandidateReasons = computed(() => selectedCandidateDetail.value?.reasons ?? ["無理由說明"]);
const selectedCandidateTags = computed(() => selectedCandidateDetail.value?.tags ?? []);
const selectedCandidateWatchlists = computed(() => selectedCandidateDetail.value?.watchlists ?? []);

const selectedCandidateContextMetrics = computed(() => {
  if (!selectedCandidateDetail.value) {
    return [];
  }
  const metrics = [
    {
      label: "標籤數",
      value: formatNumber(selectedCandidateDetail.value.tags.length),
      hint: "分類關聯",
    },
    {
      label: "觀察清單數",
      value: formatNumber(selectedCandidateDetail.value.watchlists.length),
      hint: "watchlist 關聯",
    },
    {
      label: "掃描關聯數",
      value: formatNumber(selectedCandidateDetail.value.scannerMemberships.length),
      hint: "group/watchlist scanner",
    },
  ];
  return [...metrics, ...selectedCandidateDetail.value.keyMetrics.slice(0, 3)];
});

const selectedCandidateScannerRows = computed(() =>
  (selectedCandidateDetail.value?.scannerMemberships ?? []).map((membership) => ({
    scanner_key: `${membership.kind}-${membership.name}`,
    name: membership.name,
    kind: membership.kind === "watchlist" ? "觀察清單" : "標籤群組",
    flagged: membership.flagged ? "是" : "否",
    reasons: formatList(membership.flagReasons, membership.flagged ? "已命中" : "未命中"),
  })),
);

const candidateReportLink = computed(() => ({
  name: "reports",
  query: {
    reportDate: selectedCandidateItem.value?.candidate_date ?? candidateDate.value ?? undefined,
  },
}));

const candidateGroupLink = computed(() => {
  const firstTag = selectedCandidateTags.value[0];
  if (!firstTag) {
    return null;
  }
  return {
    name: "groups",
    query: {
      tag: firstTag,
      tradeDate: selectedCandidateItem.value?.candidate_date ?? undefined,
    },
  };
});

const candidateWatchlistsLink = computed(() => {
  if (!selectedCandidateWatchlists.value.length) {
    return null;
  }
  return {
    name: "watchlists",
    query: {
      tradeDate: selectedCandidateItem.value?.candidate_date ?? undefined,
    },
  };
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
    syncRouteQuery();
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

function syncRouteQuery(): void {
  void router.replace({
    query: {
      candidateDate: candidateDate.value || undefined,
      limit: String(limit.value),
      run: selectedRunId.value ? String(selectedRunId.value) : undefined,
      search: searchQuery.value || undefined,
      sortBy: candidateSortBy.value || undefined,
      sortDirection: candidateSortDirection.value || undefined,
    },
  });
}

onMounted(() => {
  candidateDate.value = typeof route.query.candidateDate === "string" ? route.query.candidateDate : "";
  searchQuery.value = typeof route.query.search === "string" ? route.query.search : "";
  limit.value = typeof route.query.limit === "string" ? Number(route.query.limit) : 10;
  selectedRunId.value = typeof route.query.run === "string" ? Number(route.query.run) : null;
  candidateSortBy.value = typeof route.query.sortBy === "string" ? route.query.sortBy : "score";
  candidateSortDirection.value =
    route.query.sortDirection === "asc" || route.query.sortDirection === "desc"
      ? route.query.sortDirection
      : "desc";
  return loadCandidates();
});

watch([searchQuery, candidateSortBy, candidateSortDirection, selectedRunId], syncRouteQuery);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.5rem;
}

.detail-grid {
  margin-bottom: 1rem;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.detail-link {
  color: var(--accent);
  text-decoration: none;
}

.detail-link:hover {
  text-decoration: underline;
}

.detail-list {
  margin: 0;
  padding-left: 1.1rem;
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 0.75rem;
}
</style>
