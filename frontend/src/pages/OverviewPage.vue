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
    <EmptyState
      v-else-if="overview?.meta.is_empty"
      title="No dashboard data yet"
      message="Run seed, sample ETL, indicators, and reports to populate the overview."
    />
    <template v-else-if="overview">
      <SummaryCardGrid :cards="overview.summary_cards" />

      <section class="panel">
        <div class="panel-header">
          <h2>Highlights</h2>
          <span class="pill info">As of {{ overview.meta.as_of_date ?? "n/a" }}</span>
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in overview.highlights" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>

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
import { onMounted, ref } from "vue";

import { fetchOverview } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { DashboardOverviewRead } from "@/types/dashboard";

const overview = ref<DashboardOverviewRead | null>(null);
const isLoading = ref(false);
const selectedTag = ref("semiconductor");
const selectedWatchlistId = ref("");
const watchlistsStore = useWatchlistsStore();

async function loadOverview(): Promise<void> {
  isLoading.value = true;
  try {
    overview.value = await fetchOverview({
      watchlistId: selectedWatchlistId.value ? Number(selectedWatchlistId.value) : undefined,
      tag: selectedTag.value || undefined,
      topN: 5,
    });
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
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.6rem;
}
</style>
