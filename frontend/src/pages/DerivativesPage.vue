<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Derivatives"
      description="Taiwan institutional derivatives bias summary, anomaly counts, and highlight lines."
    />

    <LoadingState v-if="isLoading" message="Loading derivatives dashboard..." />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No derivatives summary"
      message="Run the Taiwan derivatives pipeline before opening this page."
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

import { fetchDerivativesDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { DerivativesDashboardRead } from "@/types/dashboard";

const dashboard = ref<DerivativesDashboardRead | null>(null);
const isLoading = ref(false);

async function loadDerivatives(): Promise<void> {
  isLoading.value = true;
  try {
    dashboard.value = await fetchDerivativesDashboard();
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadDerivatives);
</script>
