<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="觀察清單"
      description="查看清單級別的每日快照、摘要卡片、掃描旗標與成員狀態。"
    />

    <FilterBar
      title="清單篩選"
      description="切換觀察清單，查看成員、掃描訊號與摘要指標。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="watchlist-trade-date">交易日期</label>
          <input id="watchlist-trade-date" v-model="tradeDate" type="date" />
        </div>
        <div class="field-group">
          <label for="watchlist-select">觀察清單</label>
          <select id="watchlist-select" v-model="selectedWatchlistId" @change="loadWatchlist">
            <option v-for="watchlist in watchlistsStore.items" :key="watchlist.id" :value="String(watchlist.id)">
              {{ watchlist.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadWatchlist">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="清單資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="觀察清單頁整合成員、摘要指標與掃描旗標。"
      demo-hint="若尚無資料，請執行 make demo-data 產生示範快照。"
      :show-refresh="true"
      @refresh="loadWatchlist"
    />

    <LoadingState v-if="isLoading" message="正在載入觀察清單..." />
    <ErrorState
      v-else-if="errorMessage"
      title="觀察清單載入失敗"
      message="無法從後端載入指定的觀察清單資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無清單資料"
      message="後端目前還沒有觀察清單快照。執行 make demo-data 後即可產生日線、掃描輸入與報表相關資料。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="清單快照" :description="selectedWatchlistDescription">
          <template #header>
            <RouterLink
              :to="{ name: 'overview', query: { watchlistId: selectedWatchlistId, tradeDate: tradeDate || undefined } }"
              class="pill link-pill"
            >
              回到總覽查看
            </RouterLink>
          </template>
          <MetricGrid :metrics="watchlistMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="清單強弱分布"
          description="顯示目前清單的日內表現與廣度指標。"
          :points="watchlistChartPoints"
          empty-message="目前沒有清單圖表資料。"
        />
      </div>

      <DetailPanel title="清單重點" description="整理目前觀察清單最值得注意的訊號。">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="掃描旗標"
          description="顯示觀察清單掃描器標記出的標的。"
          :columns="flagColumns"
          :rows="flagRows"
          default-sort-by="change_pct"
          default-sort-direction="desc"
          empty-message="目前清單沒有掃描旗標。"
        />
        <SortableTableSection
          title="清單成員"
          description="顯示後端回傳的目前觀察清單成員。"
          :columns="itemColumns"
          :rows="itemRows"
          default-sort-by="instrument_id"
          default-sort-direction="asc"
          empty-message="目前沒有清單成員。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { fetchWatchlistDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchWatchlistItems } from "@/api/watchlists";
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
import { useWatchlistsStore } from "@/stores/watchlists";
import type { WatchlistItemRead } from "@/types/api";
import type { WatchlistDashboardRead } from "@/types/dashboard";
import { formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const watchlistsStore = useWatchlistsStore();
const selectedWatchlistId = ref("");
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const dashboard = ref<WatchlistDashboardRead | null>(null);
const items = ref<WatchlistItemRead[]>([]);
const tradeDate = ref("");
const route = useRoute();
const router = useRouter();

const selectedWatchlistDescription = computed(
  () =>
    watchlistsStore.items.find((watchlist) => String(watchlist.id) === selectedWatchlistId.value)?.description ??
    "顯示最新摘要、掃描廣度與成員狀態。",
);

const itemColumns = [
  { key: "instrument_id", label: "標的 ID" },
  { key: "added_at", label: "加入時間" },
];

const flagColumns = [
  { key: "symbol", label: "代號" },
  { key: "change_pct", label: "漲跌幅 %" },
  { key: "volume_ratio", label: "量比" },
  { key: "reasons", label: "原因" },
];

const itemRows = computed(() =>
  items.value.map((item) => ({
    instrument_id: item.instrument_id,
    added_at: formatDateTime(item.created_at),
  })),
);

const flagRows = computed(() =>
  dashboard.value?.data?.scanner?.flagged_instruments.map((item) => ({
    symbol: makeLinkedCell(item.symbol, { name: "candidates", query: { search: item.symbol } }),
    change_pct: Number(item.close_change_pct),
    volume_ratio: item.volume_ratio ? Number(item.volume_ratio) : null,
    reasons: formatList(item.reasons, "無理由說明"),
  })) ?? [],
);

const watchlistMetrics = computed(() => {
  const snapshot = dashboard.value?.data;
  if (!snapshot) {
    return [];
  }
  return [
    { label: "成員數", value: formatNumber(snapshot.summary.member_count), hint: "清單規模" },
    { label: "平均漲跌", value: formatPercent(snapshot.summary.average_close_change_pct), hint: "每日變化" },
    {
      label: "站上 SMA",
      value: formatPercent(snapshot.summary.percentage_above_sma),
      hint: "廣度",
    },
    {
      label: "旗標數",
      value: formatNumber(snapshot.scanner?.flagged_instruments.length ?? 0),
      hint: "掃描命中",
    },
  ];
});

const watchlistChartPoints = computed(() => {
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

async function loadWatchlist(): Promise<void> {
  if (!selectedWatchlistId.value) {
    return;
  }
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const watchlistId = Number(selectedWatchlistId.value);
    const [dashboardResponse, itemsResponse] = await Promise.all([
      fetchWatchlistDashboard(watchlistId, { tradeDate: tradeDate.value || undefined }),
      fetchWatchlistItems(watchlistId),
    ]);
    dashboard.value = dashboardResponse;
    items.value = itemsResponse;
    await router.replace({
      query: {
        watchlistId: selectedWatchlistId.value || undefined,
        tradeDate: tradeDate.value || undefined,
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  await watchlistsStore.load();
  selectedWatchlistId.value = typeof route.query.watchlistId === "string" ? route.query.watchlistId : "";
  tradeDate.value = typeof route.query.tradeDate === "string" ? route.query.tradeDate : "";
  if (!selectedWatchlistId.value && watchlistsStore.items[0]) {
    selectedWatchlistId.value = String(watchlistsStore.items[0].id);
  }
  if (selectedWatchlistId.value) {
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

.link-pill {
  text-decoration: none;
}
</style>
