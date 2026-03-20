<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Watchlists"
      description="Watchlist-level daily snapshot with summary cards, scanner flags, and ranked movers."
    />

    <FilterBar
      title="Watchlist Scope"
      description="Switch watchlists and inspect scanner signals, membership, and summary metrics."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="watchlist-trade-date">Trade Date</label>
          <input id="watchlist-trade-date" v-model="tradeDate" type="date" />
        </div>
        <div class="field-group">
          <label for="watchlist-select">Watchlist</label>
          <select id="watchlist-select" v-model="selectedWatchlistId" @change="loadWatchlist">
            <option v-for="watchlist in watchlistsStore.items" :key="watchlist.id" :value="String(watchlist.id)">
              {{ watchlist.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadWatchlist">Refresh</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="Watchlist Data Status"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="Watchlists combine membership, summary metrics, and scanner flags."
      demo-hint="Run make demo-data to populate watchlist snapshots."
      :show-refresh="true"
      @refresh="loadWatchlist"
    />

    <LoadingState v-if="isLoading" message="Loading watchlist dashboard..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Watchlist request failed"
      message="The selected watchlist could not be loaded from the backend."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No watchlist data"
      message="The backend has no watchlist snapshot data yet. Run make demo-data to generate daily bars, scanner inputs, and reports."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="Watchlist Snapshot" :description="selectedWatchlistDescription">
          <template #header>
            <RouterLink
              :to="{ name: 'overview', query: { watchlistId: selectedWatchlistId, tradeDate: tradeDate || undefined } }"
              class="pill link-pill"
            >
              Open in overview
            </RouterLink>
          </template>
          <MetricGrid :metrics="watchlistMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="Watchlist Balance"
          description="Daily performance and breadth metrics for the selected watchlist."
          :points="watchlistChartPoints"
          empty-message="No watchlist chart data available."
        />
      </div>

      <DetailPanel title="Watchlist Highlights" description="Top signals for the selected watchlist.">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="Scanner Flags"
          description="Flagged instruments from the watchlist scanner output."
          :columns="flagColumns"
          :rows="flagRows"
          default-sort-by="change_pct"
          default-sort-direction="desc"
          empty-message="No flagged instruments for the selected watchlist."
        />
        <SortableTableSection
          title="Watchlist Items"
          description="Current watchlist membership returned by the backend."
          :columns="itemColumns"
          :rows="itemRows"
          default-sort-by="instrument_id"
          default-sort-direction="asc"
          empty-message="No watchlist items found."
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { fetchWatchlistDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchWatchlistItems } from "@/api/watchlists";
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
import { useWatchlistsStore } from "@/stores/watchlists";
import type { WatchlistItemRead } from "@/types/api";
import type { WatchlistDashboardRead } from "@/types/dashboard";
import { formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const watchlistsStore = useWatchlistsStore();
const selectedWatchlistId = ref("");
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const dashboard = ref<WatchlistDashboardRead | null>(null);
const items = ref<WatchlistItemRead[]>([]);
const tradeDate = ref("");
const route = useRoute();
const router = useRouter();

const selectedWatchlistDescription = computed(
  () =>
    watchlistsStore.items.find((watchlist) => String(watchlist.id) === selectedWatchlistId.value)?.description ??
    "Latest summary, scanner breadth, and membership state.",
);

const itemColumns = [
  { key: "instrument_id", label: "Instrument ID" },
  { key: "added_at", label: "Added" },
];

const flagColumns = [
  { key: "symbol", label: "Symbol" },
  { key: "change_pct", label: "Change %" },
  { key: "volume_ratio", label: "Volume Ratio" },
  { key: "reasons", label: "Reasons" },
];

const itemRows = computed(() =>
  items.value.map((item) => ({
    instrument_id: item.instrument_id,
    added_at: formatDateTime(item.created_at),
  })),
);

const flagRows = computed(() =>
  dashboard.value?.data?.scanner?.flagged_instruments.map((item) => ({
    symbol: makeLinkedCell(item.symbol, { name: "candidates", query: { search: item.symbol } }),
    change_pct: Number(item.close_change_pct),
    volume_ratio: item.volume_ratio ? Number(item.volume_ratio) : null,
    reasons: formatList(item.reasons, "No reasons"),
  })) ?? [],
);

const watchlistMetrics = computed(() => {
  const snapshot = dashboard.value?.data;
  if (!snapshot) {
    return [];
  }
  return [
    { label: "Members", value: formatNumber(snapshot.summary.member_count), hint: "watchlist size" },
    { label: "Average Change", value: formatPercent(snapshot.summary.average_close_change_pct), hint: "daily move" },
    {
      label: "Above SMA",
      value: formatPercent(snapshot.summary.percentage_above_sma),
      hint: "breadth",
    },
    {
      label: "Flags",
      value: formatNumber(snapshot.scanner?.flagged_instruments.length ?? 0),
      hint: "scanner matches",
    },
  ];
});

const watchlistChartPoints = computed(() => {
  const snapshot = dashboard.value?.data;
  if (!snapshot) {
    return [];
  }
  return [
    {
      label: "Avg Return",
      value: Number(snapshot.scanner?.average_daily_return_pct ?? snapshot.summary.average_close_change_pct),
      tone: "info" as const,
    },
    {
      label: "Above SMA",
      value: Number(snapshot.summary.percentage_above_sma),
      tone: "positive" as const,
    },
    {
      label: "Volume Ratio",
      value: Number(snapshot.scanner?.average_volume_ratio ?? 0),
      tone: "neutral" as const,
    },
  ];
});

async function loadWatchlist(): Promise<void> {
  if (!selectedWatchlistId.value) {
    return;
  }
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const watchlistId = Number(selectedWatchlistId.value);
    const [dashboardResponse, itemsResponse] = await Promise.all([
      fetchWatchlistDashboard(watchlistId, { tradeDate: tradeDate.value || undefined }),
      fetchWatchlistItems(watchlistId),
    ]);
    dashboard.value = dashboardResponse;
    items.value = itemsResponse;
    await router.replace({
      query: {
        watchlistId: selectedWatchlistId.value || undefined,
        tradeDate: tradeDate.value || undefined,
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
  selectedWatchlistId.value = typeof route.query.watchlistId === "string" ? route.query.watchlistId : "";
  tradeDate.value = typeof route.query.tradeDate === "string" ? route.query.tradeDate : "";
  if (!selectedWatchlistId.value && watchlistsStore.items[0]) {
    selectedWatchlistId.value = String(watchlistsStore.items[0].id);
  }
  if (selectedWatchlistId.value) {
    await loadWatchlist();
  }
});
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.5rem;
}

.link-pill {
  text-decoration: none;
}
</style>
