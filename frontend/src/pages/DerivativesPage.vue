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
      message="The backend has no Taiwan derivatives summary yet. Run make demo-data to generate a repeatable local derivatives dataset."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="Bias Metrics" description="Latest institutional derivatives regime and signal balance.">
          <MetricGrid :metrics="metricCards" />
        </DetailPanel>
        <MiniBarChart
          title="Regime Composition"
          description="Bullish, bearish, neutral, and anomaly counts from the latest summary."
          :points="chartPoints"
          empty-message="No derivatives composition available."
        />
      </div>

      <DetailPanel title="Bias Context" description="Headline observations from the derivatives summary.">
        <ul class="highlights">
          <li v-for="item in (summary?.highlights ?? dashboard.highlights)" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="Bias Metrics Table"
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
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
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
    { metric: "Average Bias Score", value: Number(summary.value.average_bias_score) },
    { metric: "Bullish Rows", value: summary.value.bullish_count },
    { metric: "Bearish Rows", value: summary.value.bearish_count },
    { metric: "Anomalies", value: summary.value.anomaly_count },
  ];
});

const metricCards = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { label: "Trade Date", value: summary.value.trade_date, hint: "latest stored summary" },
    { label: "Regime", value: summary.value.overall_regime, hint: "market-level context" },
    { label: "Bias Score", value: formatNumber(summary.value.average_bias_score), hint: "aggregate score" },
    { label: "Anomalies", value: formatNumber(summary.value.anomaly_count), hint: "feature outliers" },
  ];
});

const chartPoints = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { label: "Bullish", value: summary.value.bullish_count, tone: "positive" as const },
    { label: "Bearish", value: summary.value.bearish_count, tone: "negative" as const },
    { label: "Neutral", value: summary.value.neutral_count, tone: "neutral" as const },
    { label: "Anomalies", value: summary.value.anomaly_count, tone: "info" as const },
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
