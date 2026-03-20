<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Derivatives"
      description="Taiwan institutional derivatives bias summary, anomaly counts, and highlight lines."
    />

    <LoadingState v-if="isLoading" message="Loading derivatives dashboard..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Derivatives request failed"
      message="The latest Taiwan institutional summary could not be loaded."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No derivatives summary"
      message="Run the Taiwan derivatives pipeline before opening this page."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />
      <section class="panel">
        <div class="panel-header">
          <SectionHeader title="Bias Context" description="Latest institutional derivatives regime and highlight lines." />
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in (summary?.highlights ?? dashboard.highlights)" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>
      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <TableSection
          title="Bias Metrics"
          description="Direct summary fields from the derivatives API."
          :columns="metricColumns"
          :rows="metricRows"
          empty-message="No derivatives metrics available."
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchDerivativesDashboard } from "@/api/dashboard";
import { fetchLatestDerivativesSummary } from "@/api/derivatives";
import { normalizeApiError } from "@/api/http";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import type { DailyInstitutionalBiasSummary, DerivativesDashboardRead } from "@/types/dashboard";
import { formatNumber } from "@/utils/formatters";

const dashboard = ref<DerivativesDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const summary = ref<DailyInstitutionalBiasSummary | null>(null);

const metricColumns = [
  { key: "metric", label: "Metric" },
  { key: "value", label: "Value" },
];

const metricRows = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { metric: "Trade Date", value: summary.value.trade_date },
    { metric: "Overall Regime", value: summary.value.overall_regime },
    { metric: "Average Bias Score", value: formatNumber(summary.value.average_bias_score) },
    { metric: "Bullish Rows", value: formatNumber(summary.value.bullish_count) },
    { metric: "Bearish Rows", value: formatNumber(summary.value.bearish_count) },
    { metric: "Anomalies", value: formatNumber(summary.value.anomaly_count) },
  ];
});

async function loadDerivatives(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [dashboardResponse, summaryResponse] = await Promise.all([
      fetchDerivativesDashboard(),
      fetchLatestDerivativesSummary(),
    ]);
    dashboard.value = dashboardResponse;
    summary.value = summaryResponse;
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadDerivatives);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
}
</style>
