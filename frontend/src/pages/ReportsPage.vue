<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Reports"
      description="Latest generated reports, report bundle outputs, and report types ready for frontend display."
    />

    <LoadingState v-if="isLoading" message="Loading reports dashboard..." />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No reports available"
      message="Generate reports from the backend workflow first."
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

import { fetchReportsDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { ReportsDashboardRead } from "@/types/dashboard";

const dashboard = ref<ReportsDashboardRead | null>(null);
const isLoading = ref(false);

async function loadReports(): Promise<void> {
  isLoading.value = true;
  try {
    dashboard.value = await fetchReportsDashboard({ limit: 10 });
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadReports);
</script>
