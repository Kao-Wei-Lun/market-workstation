<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Overview"
      description="Daily market breadth, candidates, groups, reports, and the latest research signals."
    >
      <div class="form-inline">
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
    </PageHeader>

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
      message="Run seed, sample ETL, indicators, and reports to populate the overview."
    />
    <template v-else-if="overview">
      <SummaryCardGrid :cards="overview.summary_cards" />

      <section class="panel">
        <div class="panel-header">
          <SectionHeader title="Highlights" description="Top-level review points for the selected dashboard scope.">
            <span class="pill info">As of {{ overview.meta.as_of_date ?? "n/a" }}</span>
          </SectionHeader>
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in overview.highlights" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>

      <div class="page-section-grid">
        <section class="panel">
          <div class="panel-header">
            <SectionHeader title="Market Snapshot" description="Latest stored breadth metrics from daily bars." />
          </div>
          <div class="panel-body">
            <dl v-if="overview.data.market_snapshot" class="metric-list">
              <div>
                <dt>Instruments</dt>
                <dd>{{ formatNumber(overview.data.market_snapshot.instrument_count) }}</dd>
              </div>
              <div>
                <dt>Advancers</dt>
                <dd>{{ formatNumber(overview.data.market_snapshot.advancers) }}</dd>
              </div>
              <div>
                <dt>Decliners</dt>
                <dd>{{ formatNumber(overview.data.market_snapshot.decliners) }}</dd>
              </div>
              <div>
                <dt>Above SMA20</dt>
                <dd>{{ formatPercent(overview.data.market_snapshot.percentage_above_sma20) }}</dd>
              </div>
            </dl>
            <p v-else class="muted">No market snapshot data available.</p>
          </div>
        </section>

        <TableSection
          title="Top Candidates"
          description="Highest-ranked next-day candidates from the latest stored run."
          :columns="candidateColumns"
          :rows="candidateRows"
          empty-message="No candidate items available."
        />

        <TableSection
          title="Recent Reports"
          description="Latest persisted reports for the selected report date."
          :columns="reportColumns"
          :rows="reportRows"
          empty-message="No reports available."
        />

        <TableSection
          title="Recent Backtests"
          description="Most recent backtest runs available to the dashboard."
          :columns="backtestColumns"
          :rows="backtestRows"
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

import { fetchOverview } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { DashboardOverviewRead } from "@/types/dashboard";
import { formatDate, formatNumber, formatPercent } from "@/utils/formatters";

const overview = ref<DashboardOverviewRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedTag = ref("semiconductor");
const selectedWatchlistId = ref("");
const watchlistsStore = useWatchlistsStore();

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
    symbol: item.symbol,
    score: formatNumber(item.score),
    reasons: item.candidate_reasons.join(", "),
  })) ?? [],
);

const reportRows = computed(() =>
  overview.value?.data.report_summary?.reports.map((report) => ({
    date: formatDate(report.report_date),
    type: report.report_type,
    title: report.title,
  })) ?? [],
);

const backtestRows = computed(() =>
  overview.value?.data.backtest_summary?.recent_runs.map((run) => ({
    run_id: `#${run.id}`,
    return_pct: formatPercent(run.total_return_pct),
    trades: formatNumber(run.total_trades),
    status: run.status,
  })) ?? [],
);

async function loadOverview(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    overview.value = await fetchOverview({
      watchlistId: selectedWatchlistId.value ? Number(selectedWatchlistId.value) : undefined,
      tag: selectedTag.value || undefined,
      topN: 5,
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  await watchlistsStore.load();
  if (watchlistsStore.items[0]) {
    selectedWatchlistId.value = String(watchlistsStore.items[0].id);
  }
  await loadOverview();
});
</script>

<style scoped>
.metric-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin: 0;
}

.metric-list div {
  padding: 0.85rem;
  border-radius: 14px;
  background: var(--panel-alt);
}

.metric-list dt {
  color: var(--muted);
  font-size: 0.82rem;
}

.metric-list dd {
  margin: 0.25rem 0 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.6rem;
}
</style>
