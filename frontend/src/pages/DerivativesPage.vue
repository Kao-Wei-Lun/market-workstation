<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="衍生性商品"
      description="查看台灣法人衍生性商品偏向摘要、異常數與重點觀察。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'market-charts' }">查看市場結構圖</RouterLink>
      </div>
    </PageHeader>

    <FilterBar
      title="衍生性商品檢視"
      description="檢視最新台灣法人衍生性商品快照，並在本機 demo 資料更新後重新整理。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadDerivatives">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="衍生性商品資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="衍生性商品頁的重點內容來自法人日摘要資料。"
      demo-hint="若衍生性商品頁為空，請執行 make demo-data 產生示範資料。"
      :show-refresh="true"
      @refresh="loadDerivatives"
    />

    <LoadingState v-if="isLoading" message="正在載入衍生性商品資料..." />
    <ErrorState
      v-else-if="errorMessage"
      title="衍生性商品載入失敗"
      message="無法載入最新台灣法人摘要資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無衍生性商品摘要"
      message="後端目前沒有台灣法人衍生性商品摘要。執行 make demo-data 後即可產生可重複的本機示範資料。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="偏向指標" description="顯示最新法人衍生性商品 regime 與訊號分布。">
          <MetricGrid :metrics="metricCards" />
        </DetailPanel>
        <MiniBarChart
          title="市場狀態組成"
          description="顯示最新摘要中的偏多、偏空、中性與異常筆數。"
          :points="chartPoints"
          empty-message="目前沒有衍生性商品組成資料。"
        />
      </div>

      <DetailPanel title="偏向脈絡" description="整理衍生性商品摘要中的主要觀察。">
        <ul class="highlights">
          <li v-for="item in (summary?.highlights ?? dashboard.highlights)" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="偏向指標表"
          description="顯示衍生性商品 API 回傳的直接摘要欄位。"
          :columns="metricColumns"
          :rows="metricRows"
          empty-message="目前沒有衍生性商品指標。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { fetchDerivativesDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
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
import type { DailyInstitutionalBiasSummary, DerivativesDashboardRead } from "@/types/dashboard";
import { formatDateTime, formatNumber } from "@/utils/formatters";

const dashboard = ref<DerivativesDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const summary = ref<DailyInstitutionalBiasSummary | null>(null);

const metricColumns = [
  { key: "metric", label: "指標" },
  { key: "value", label: "數值" },
];

const metricRows = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { metric: "交易日期", value: summary.value.trade_date },
    { metric: "整體市場狀態", value: summary.value.overall_regime },
    { metric: "平均偏向分數", value: Number(summary.value.average_bias_score) },
    { metric: "偏多筆數", value: summary.value.bullish_count },
    { metric: "偏空筆數", value: summary.value.bearish_count },
    { metric: "異常數", value: summary.value.anomaly_count },
  ];
});

const metricCards = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { label: "交易日期", value: summary.value.trade_date, hint: "最新保存摘要" },
    { label: "市場狀態", value: summary.value.overall_regime, hint: "市場層級脈絡" },
    { label: "偏向分數", value: formatNumber(summary.value.average_bias_score), hint: "整體分數" },
    { label: "異常數", value: formatNumber(summary.value.anomaly_count), hint: "特徵異常值" },
  ];
});

const chartPoints = computed(() => {
  if (!summary.value) {
    return [];
  }
  return [
    { label: "偏多", value: summary.value.bullish_count, tone: "positive" as const },
    { label: "偏空", value: summary.value.bearish_count, tone: "negative" as const },
    { label: "中性", value: summary.value.neutral_count, tone: "neutral" as const },
    { label: "異常", value: summary.value.anomaly_count, tone: "info" as const },
  ];
});

async function loadDerivatives(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const dashboardResponse = await fetchDerivativesDashboard();
    dashboard.value = dashboardResponse;
    summary.value = dashboardResponse.data;
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

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}
</style>
