<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Overview"
      description="Daily market breadth, candidates, groups, reports, and the latest research signals."
    >
      <div class="page-actions">
        <RouterLink
          v-if="selectedWatchlistId"
          class="pill link-pill"
          :to="{ name: 'watchlists', query: { watchlistId: selectedWatchlistId, tradeDate: selectedTradeDate || undefined } }"
        >
          Open watchlist
        </RouterLink>
        <RouterLink
          v-if="selectedTag"
          class="pill link-pill"
          :to="{ name: 'groups', query: { tag: selectedTag, tradeDate: selectedTradeDate || undefined } }"
        >
          Open group
        </RouterLink>
      </div>
    </PageHeader>

    <FilterBar
      title="Overview Scope"
      description="Adjust the watchlist and tag scope used by the aggregate dashboard endpoint."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="overview-trade-date">Trade Date</label>
          <input id="overview-trade-date" v-model="selectedTradeDate" type="date" />
        </div>
        <div class="field-group">
          <label for="overview-watchlist">Watchlist</label>
          <select id="overview-watchlist" v-model="selectedWatchlistId">
            <option value="">None</option>
            <option v-for="watchlist in watchlistsStore.items" :key="watchlist.id" :value="String(watchlist.id)">
              {{ watchlist.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="overview-tag">Tag</label>
          <input id="overview-tag" v-model="selectedTag" placeholder="semiconductor" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadOverview">Refresh</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="Overview Data Status"
      :as-of-date="overview?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(overview?.meta.generated_at)"
      :item-count="overview?.meta.item_count"
      hint="Use trade date, watchlist, and tag together to narrow the dashboard scope."
      demo-hint="Run make demo-data if the dashboard is still empty."
      :show-refresh="true"
      @refresh="loadOverview"
    />

    <LoadingState v-if="isLoading" message="Loading dashboard overview..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Overview request failed"
      message="The overview page could not load backend dashboard data."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="overview?.meta.is_empty"
      title="No dashboard data yet"
      message="The backend has no visible market data yet. Run make demo-data to populate overview cards, reports, candidates, derivatives, and backtests."
    />
    <template v-else-if="overview">
      <SummaryCardGrid :cards="overview.summary_cards" />

      <DetailPanel
        title="Session Highlights"
        description="Top-level review points for the selected dashboard scope."
      >
        <template #header>
          <span class="pill info">As of {{ overview.meta.as_of_date ?? "n/a" }}</span>
        </template>
        <ul class="highlights">
          <li v-for="item in overview.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <MetricGrid :metrics="marketMetrics" />
        <MiniBarChart
          title="Breadth Snapshot"
          description="Advancers, decliners, and unchanged names from the latest market summary."
          :points="breadthChartPoints"
          empty-message="No breadth data available."
        />
        <MiniBarChart
          title="Candidate Score Ladder"
          description="Top candidate scores from the latest candidate run."
          :points="candidateChartPoints"
          empty-message="No candidate scores available."
        />
      </div>

      <div class="page-section-grid">
        <SortableTableSection
          title="Top Candidates"
          description="Highest-ranked next-day candidates from the latest stored run."
          :columns="candidateColumns"
          :rows="candidateRows"
          default-sort-by="score"
          default-sort-direction="desc"
          empty-message="No candidate items available."
        />
        <SortableTableSection
          title="Recent Reports"
          description="Latest persisted reports for the selected report date."
          :columns="reportColumns"
          :rows="reportRows"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="No reports available."
        />
        <SortableTableSection
          title="Recent Backtests"
          description="Most recent backtest runs available to the dashboard."
          :columns="backtestColumns"
          :rows="backtestRows"
          default-sort-by="return_pct"
          default-sort-direction="desc"
          empty-message="No backtests available."
        />
      </div>

      <div class="page-section-grid">
        <RankedListSection
          v-for="list in overview.ranked_lists"
          :key="list.key"
          :list="list"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { fetchOverview } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { DashboardOverviewRead } from "@/types/dashboard";
import { formatDate, formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const overview = ref<DashboardOverviewRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedTag = ref("semiconductor");
const selectedWatchlistId = ref("");
const selectedTradeDate = ref("");
const watchlistsStore = useWatchlistsStore();
const route = useRoute();
const router = useRouter();

const candidateColumns = [
  { key: "rank", label: "Rank" },
  { key: "symbol", label: "Symbol" },
  { key: "score", label: "Score" },
  { key: "reasons", label: "Reasons" },
];

const reportColumns = [
  { key: "date", label: "Date" },
  { key: "type", label: "Type" },
  { key: "title", label: "Title" },
];

const backtestColumns = [
  { key: "run_id", label: "Run" },
  { key: "return_pct", label: "Return %" },
  { key: "trades", label: "Trades" },
  { key: "status", label: "Status" },
];

const candidateRows = computed(() =>
  overview.value?.data.candidate_summary?.top_items.map((item) => ({
    rank: item.rank,
    symbol: makeLinkedCell(item.symbol, {
      name: "candidates",
      query: {
        run: String(overview.value?.data.candidate_summary?.run.id ?? ""),
        search: item.symbol,
        candidateDate: item.candidate_date,
      },
    }),
    score: Number(item.score),
    reasons: formatList(item.candidate_reasons, "No reasons"),
  })) ?? [],
);

const reportRows = computed(() =>
  overview.value?.data.report_summary?.reports.map((report) => ({
    date: formatDate(report.report_date),
    type: report.report_type,
    title: makeLinkedCell(report.title, {
      name: "reports",
      query: {
        reportDate: report.report_date,
        reportType: report.report_type,
      },
    }),
  })) ?? [],
);

const backtestRows = computed(() =>
  overview.value?.data.backtest_summary?.recent_runs.map((run) => ({
    run_id: makeLinkedCell(`#${run.id}`, { name: "backtests", query: { run: String(run.id) } }),
    return_pct: Number(run.total_return_pct),
    trades: run.total_trades,
    status: run.status,
  })) ?? [],
);

const marketMetrics = computed(() => {
  const marketSnapshot = overview.value?.data.market_snapshot;
  if (!marketSnapshot) {
    return [];
  }
  return [
    { label: "Instruments", value: formatNumber(marketSnapshot.instrument_count), hint: "tracked daily bars" },
    { label: "Average Change", value: formatPercent(marketSnapshot.average_close_change_pct), hint: "close-to-close" },
    { label: "Above SMA20", value: formatPercent(marketSnapshot.percentage_above_sma20), hint: "breadth strength" },
    {
      label: "Top Candidate Count",
      value: formatNumber(overview.value?.data.candidate_summary?.top_items.length ?? 0),
      hint: "ranked names",
    },
  ];
});

const breadthChartPoints = computed(() => {
  const marketSnapshot = overview.value?.data.market_snapshot;
  if (!marketSnapshot) {
    return [];
  }
  return [
    { label: "Advancers", value: marketSnapshot.advancers, tone: "positive" as const },
    { label: "Decliners", value: marketSnapshot.decliners, tone: "negative" as const },
    { label: "Unchanged", value: marketSnapshot.unchanged, tone: "neutral" as const },
  ];
});

const candidateChartPoints = computed(() =>
  overview.value?.data.candidate_summary?.top_items.map((item) => ({
    label: item.symbol,
    value: Number(item.score),
    tone: "info" as const,
  })) ?? [],
);

async function loadOverview(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    overview.value = await fetchOverview({
      tradeDate: selectedTradeDate.value || undefined,
      watchlistId: selectedWatchlistId.value ? Number(selectedWatchlistId.value) : undefined,
      tag: selectedTag.value || undefined,
      topN: 5,
    });
    await router.replace({
      query: {
        tradeDate: selectedTradeDate.value || undefined,
        watchlistId: selectedWatchlistId.value || undefined,
        tag: selectedTag.value || undefined,
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  await watchlistsStore.load();
  selectedTradeDate.value = typeof route.query.tradeDate === "string" ? route.query.tradeDate : "";
  selectedTag.value = typeof route.query.tag === "string" ? route.query.tag : "semiconductor";
  selectedWatchlistId.value = typeof route.query.watchlistId === "string" ? route.query.watchlistId : "";
  if (!selectedWatchlistId.value && watchlistsStore.items[0]) {
    selectedWatchlistId.value = String(watchlistsStore.items[0].id);
  }
  await loadOverview();
});
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.6rem;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.link-pill {
  text-decoration: none;
}
</style>
