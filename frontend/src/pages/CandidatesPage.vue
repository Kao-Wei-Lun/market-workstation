<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Candidates"
      description="Next-day watch candidates ranked from the backend scoring and scanner context."
    />

    <FilterBar
      title="Candidate Explorer"
      description="Filter and sort ranked candidate items without leaving the page."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="candidate-date">Candidate Date</label>
          <input id="candidate-date" v-model="candidateDate" type="date" />
        </div>
        <div class="field-group">
          <label for="candidate-limit">Limit</label>
          <select id="candidate-limit" v-model="limit" @change="loadCandidates">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </div>
        <div class="field-group">
          <label for="candidate-run">Run</label>
          <select id="candidate-run" v-model="selectedRunIdString" @change="loadSelectedRunItems">
            <option value="">Latest</option>
            <option v-for="run in runs" :key="run.id" :value="String(run.id)">
              #{{ run.id }} {{ formatDate(run.candidate_date) }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="candidate-query">Search</label>
          <input id="candidate-query" v-model="searchQuery" placeholder="symbol or reason" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadCandidates">Refresh</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="Candidate Data Status"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="Candidate runs combine ranking scores, reason lists, and scanner context."
      demo-hint="Run make demo-data if there are no candidate runs yet."
      :show-refresh="true"
      @refresh="loadCandidates"
    />

    <LoadingState v-if="isLoading" message="Loading candidate dashboard..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Candidate request failed"
      message="The latest candidate runs could not be loaded."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No candidate data"
      message="The backend has no candidate runs yet. Run make demo-data to generate a repeatable local candidate list."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="Selected Candidate Run" description="Current run summary and derivatives context.">
          <MetricGrid :metrics="candidateMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="Candidate Score Ranking"
          description="Quick visual ranking of the current candidate list."
          :points="candidateChartPoints"
          empty-message="No candidate scores available."
        />
      </div>

      <DetailPanel title="Candidate Context" description="Overview highlights from the latest stored candidate run.">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="Recent Candidate Runs"
          description="Recent stored runs that can be inspected in this page."
          :columns="runColumns"
          :rows="runRows"
          row-key="run_key"
          :selected-row-key="selectedRunRowKey"
          :interactive-rows="true"
          @row-select="handleRunRowSelect"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="No candidate runs available."
        />
        <SortableTableSection
          title="Selected Run Items"
          description="Ranked candidates for the selected run."
          :columns="itemColumns"
          :rows="filteredItemRows"
          row-key="item_key"
          :selected-row-key="selectedItemRowKey"
          :interactive-rows="true"
          @row-select="handleItemRowSelect"
          default-sort-by="score"
          default-sort-direction="desc"
          empty-message="No candidate items available."
        />
      </div>

      <DetailPanel
        v-if="selectedCandidateItem"
        title="Selected Candidate Detail"
        description="Reason list and supporting metrics for the highlighted candidate."
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
  { key: "run_id", label: "Run" },
  { key: "date", label: "Date" },
  { key: "status", label: "Status" },
  { key: "candidates", label: "Candidates" },
];

const itemColumns = [
  { key: "rank", label: "Rank" },
  { key: "symbol", label: "Symbol" },
  { key: "score", label: "Score" },
  { key: "reasons", label: "Reasons" },
];

const runRows = computed(() =>
  runs.value.map((run) => ({
    run_key: run.id,
    run_id: `#${run.id}${run.id === selectedRunId.value ? " (selected)" : ""}`,
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
    reasons: formatList(item.candidate_reasons, "No reasons"),
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
      label: "Candidates",
      value: formatNumber(selectedRun.value.total_candidates),
      hint: "persisted for the selected date",
    },
    {
      label: "Derivatives Regime",
      value: String(selectedRunSummaryJson.value.overall_derivatives_regime ?? "n/a"),
      hint: "market context",
    },
    {
      label: "Bias Score",
      value: summaryNumber(selectedRunSummaryJson.value.overall_derivatives_bias_score),
      hint: "summary score",
    },
    {
      label: "Universe Size",
      value: summaryNumber(selectedRunSummaryJson.value.instruments_considered),
      hint: "names evaluated",
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
    { label: "Symbol", value: selectedCandidateItem.value.symbol, hint: "selected candidate" },
    { label: "Score", value: formatNumber(selectedCandidateItem.value.score), hint: "overall rank score" },
    { label: "Reasons", value: formatList(selectedCandidateItem.value.candidate_reasons, "No reasons"), hint: "signal summary" },
    {
      label: "Metrics",
      value: JSON.stringify(selectedCandidateItem.value.supporting_metrics),
      hint: "supporting payload",
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
