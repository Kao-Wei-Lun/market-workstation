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
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No watchlist data"
      message="Select a watchlist after running seed and sample data flows."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />
      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchWatchlistDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { WatchlistDashboardRead } from "@/types/dashboard";

const watchlistsStore = useWatchlistsStore();
const selectedWatchlistId = ref("");
const isLoading = ref(false);
const dashboard = ref<WatchlistDashboardRead | null>(null);

async function loadWatchlist(): Promise<void> {
  if (!selectedWatchlistId.value) {
    return;
  }
  isLoading.value = true;
  try {
    dashboard.value = await fetchWatchlistDashboard(Number(selectedWatchlistId.value));
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
