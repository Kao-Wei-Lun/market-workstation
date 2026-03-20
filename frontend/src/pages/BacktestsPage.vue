<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Backtests"
      description="Recent backtest runs, key metrics, and the latest trade list for local research review."
    />

    <LoadingState v-if="isLoading" message="Loading backtests dashboard..." />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No backtests available"
      message="Create a backtest run from the API or sample data before using this page."
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

import { fetchBacktestsDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { BacktestsDashboardRead } from "@/types/dashboard";

const dashboard = ref<BacktestsDashboardRead | null>(null);
const isLoading = ref(false);

async function loadBacktests(): Promise<void> {
  isLoading.value = true;
  try {
    dashboard.value = await fetchBacktestsDashboard(5);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadBacktests);
</script>
