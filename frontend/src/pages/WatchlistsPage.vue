<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Watchlists"
      description="Watchlist-level daily snapshot with summary cards, scanner flags, and ranked movers."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="watchlist-select">Watchlist</label>
          <select id="watchlist-select" v-model="selectedWatchlistId" @change="loadWatchlist">
            <option v-for="watchlist in watchlistsStore.items" :key="watchlist.id" :value="String(watchlist.id)">
              {{ watchlist.name }}
            </option>
          </select>
        </div>
      </div>
    </PageHeader>

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
      message="Select a watchlist after running seed and sample data flows."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />
      <section class="panel">
        <div class="panel-header">
          <SectionHeader
            title="Watchlist Snapshot"
            :description="selectedWatchlistDescription"
          >
            <span class="pill info">As of {{ dashboard.meta.as_of_date ?? "n/a" }}</span>
          </SectionHeader>
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
          title="Watchlist Items"
          description="Current watchlist membership returned by the backend."
          :columns="itemColumns"
          :rows="itemRows"
          empty-message="No watchlist items found."
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchWatchlistDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchWatchlistItems } from "@/api/watchlists";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { WatchlistItemRead } from "@/types/api";
import type { WatchlistDashboardRead } from "@/types/dashboard";
import { formatDateTime } from "@/utils/formatters";

const watchlistsStore = useWatchlistsStore();
const selectedWatchlistId = ref("");
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const dashboard = ref<WatchlistDashboardRead | null>(null);
const items = ref<WatchlistItemRead[]>([]);

const selectedWatchlistDescription = computed(
  () =>
    watchlistsStore.items.find((watchlist) => String(watchlist.id) === selectedWatchlistId.value)?.description ??
    "Latest summary, scanner breadth, and membership state.",
);

const itemColumns = [
  { key: "instrument_id", label: "Instrument ID" },
  { key: "added_at", label: "Added" },
];

const itemRows = computed(() =>
  items.value.map((item) => ({
    instrument_id: item.instrument_id,
    added_at: formatDateTime(item.created_at),
  })),
);

async function loadWatchlist(): Promise<void> {
  if (!selectedWatchlistId.value) {
    return;
  }
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const watchlistId = Number(selectedWatchlistId.value);
    const [dashboardResponse, itemsResponse] = await Promise.all([
      fetchWatchlistDashboard(watchlistId),
      fetchWatchlistItems(watchlistId),
    ]);
    dashboard.value = dashboardResponse;
    items.value = itemsResponse;
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
</style>
