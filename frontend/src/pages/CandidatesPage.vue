<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Candidates"
      description="Next-day watch candidates ranked from the backend scoring and scanner context."
    >
      <div class="form-inline">
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
      </div>
    </PageHeader>

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
      <section class="panel">
        <div class="panel-header">
          <SectionHeader title="Candidate Context" description="Overview highlights from the latest stored candidate run." />
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>
      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <TableSection
          title="Recent Candidate Runs"
          description="Recent stored runs that can be inspected in this page."
          :columns="runColumns"
          :rows="runRows"
          empty-message="No candidate runs available."
        />
        <TableSection
          title="Selected Run Items"
          description="Ranked candidates for the selected run."
          :columns="itemColumns"
          :rows="itemRows"
          empty-message="No candidate items available."
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchCandidateRunItems, fetchCandidateRuns } from "@/api/candidates";
import { fetchCandidatesDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import type { CandidateItemRead, CandidateRunRead, CandidatesDashboardRead } from "@/types/dashboard";
import { formatDate, formatNumber } from "@/utils/formatters";

const dashboard = ref<CandidatesDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const runs = ref<CandidateRunRead[]>([]);
const items = ref<CandidateItemRead[]>([]);
const selectedRunId = ref<number | null>(null);
const selectedRunIdString = computed({
  get: () => (selectedRunId.value ? String(selectedRunId.value) : ""),
  set: (value: string) => {
    selectedRunId.value = value ? Number(value) : null;
  },
});

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
    run_id: `#${run.id}${run.id === selectedRunId.value ? " (selected)" : ""}`,
    date: formatDate(run.candidate_date),
    status: run.status,
    candidates: formatNumber(run.total_candidates),
  })),
);

const itemRows = computed(() =>
  items.value.map((item) => ({
    rank: item.rank,
    symbol: item.symbol,
    score: formatNumber(item.score),
    reasons: item.candidate_reasons.join(", "),
  })),
);

async function loadCandidates(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [dashboardResponse, runsResponse] = await Promise.all([
      fetchCandidatesDashboard({ limit: limit.value }),
      fetchCandidateRuns({ limit: limit.value }),
    ]);
    dashboard.value = dashboardResponse;
    runs.value = runsResponse;
    selectedRunId.value = dashboardResponse.data?.run.id ?? runsResponse[0]?.id ?? null;
    await loadSelectedRunItems();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedRunItems(): Promise<void> {
  items.value = selectedRunId.value ? await fetchCandidateRunItems(selectedRunId.value) : [];
}

onMounted(loadCandidates);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.5rem;
}
</style>
