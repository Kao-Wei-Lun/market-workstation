<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="標籤群組"
      description="查看標籤群組的每日廣度、摘要指標與強弱排序。"
    />

    <FilterBar
      title="群組篩選"
      description="依標籤檢視群組表現、強弱排序與掃描訊號。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="group-trade-date">交易日期</label>
          <input id="group-trade-date" v-model="tradeDate" type="date" />
        </div>
        <div class="field-group">
          <label for="group-tag">標籤</label>
          <input id="group-tag" v-model="tag" placeholder="semiconductor / ai / dividend" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadGroup">載入群組</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="群組資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="群組頁以標籤為核心，整合群組摘要與掃描結果。"
      demo-hint="若群組頁仍為空，請執行 make demo-data 產生示範資料。"
      :show-refresh="true"
      @refresh="loadGroup"
    />

    <LoadingState v-if="isLoading" message="正在載入標籤群組..." />
    <ErrorState
      v-else-if="errorMessage"
      title="群組載入失敗"
      message="無法從後端載入指定的標籤群組資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無群組資料"
      message="請改用其他標籤，或執行 make demo-data 產生本機群組指標與掃描資料。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="群組快照" description="顯示目前標籤群組的摘要指標。">
          <template #header>
            <RouterLink
              :to="{ name: 'overview', query: { tag, tradeDate: tradeDate || undefined } }"
              class="pill link-pill"
            >
              回到總覽查看
            </RouterLink>
          </template>
          <MetricGrid :metrics="groupMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="群組強弱分布"
          description="顯示群組平均報酬、廣度與量比。"
          :points="groupChartPoints"
          empty-message="目前沒有群組圖表資料。"
        />
      </div>

      <DetailPanel title="群組重點" description="整理目前標籤群組的重要觀察。">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="掃描旗標"
          description="顯示群組掃描器標記出的標的。"
          :columns="flagColumns"
          :rows="flagRows"
          default-sort-by="change_pct"
          default-sort-direction="desc"
          empty-message="目前群組沒有掃描旗標。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { fetchGroupDashboard } from "@/api/dashboard";
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
import type { GroupDashboardRead } from "@/types/dashboard";
import { formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const tag = ref("semiconductor");
const tradeDate = ref("");
const dashboard = ref<GroupDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const route = useRoute();
const router = useRouter();

const flagColumns = [
  { key: "symbol", label: "代號" },
  { key: "change_pct", label: "漲跌幅 %" },
  { key: "volume_ratio", label: "量比" },
  { key: "reasons", label: "原因" },
];

const flagRows = computed(() =>
  dashboard.value?.data?.scanner?.flagged_instruments.map((item) => ({
    symbol: makeLinkedCell(item.symbol, { name: "candidates", query: { search: item.symbol } }),
    change_pct: Number(item.close_change_pct),
    volume_ratio: item.volume_ratio ? Number(item.volume_ratio) : null,
    reasons: formatList(item.reasons, "無理由說明"),
  })) ?? [],
);

const groupMetrics = computed(() => {
  const snapshot = dashboard.value?.data;
  if (!snapshot) {
    return [];
  }
  return [
    { label: "成員數", value: formatNumber(snapshot.summary.member_count), hint: "標籤涵蓋數" },
    { label: "平均漲跌", value: formatPercent(snapshot.summary.average_close_change_pct), hint: "每日變化" },
    { label: "站上 SMA", value: formatPercent(snapshot.summary.percentage_above_sma), hint: "廣度" },
    {
      label: "掃描旗標",
      value: formatNumber(snapshot.scanner?.flagged_instruments.length ?? 0),
      hint: "訊號命中",
    },
  ];
});

const groupChartPoints = computed(() => {
  const snapshot = dashboard.value?.data;
  if (!snapshot) {
    return [];
  }
  return [
    {
      label: "平均報酬",
      value: Number(snapshot.scanner?.average_daily_return_pct ?? snapshot.summary.average_close_change_pct),
      tone: "info" as const,
    },
    {
      label: "站上 SMA",
      value: Number(snapshot.summary.percentage_above_sma),
      tone: "positive" as const,
    },
    {
      label: "量比",
      value: Number(snapshot.scanner?.average_volume_ratio ?? 0),
      tone: "neutral" as const,
    },
  ];
});

async function loadGroup(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    dashboard.value = await fetchGroupDashboard(tag.value, { tradeDate: tradeDate.value || undefined });
    await router.replace({
      query: {
        tag: tag.value || undefined,
        tradeDate: tradeDate.value || undefined,
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  tag.value = typeof route.query.tag === "string" ? route.query.tag : "semiconductor";
  tradeDate.value = typeof route.query.tradeDate === "string" ? route.query.tradeDate : "";
  return loadGroup();
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
