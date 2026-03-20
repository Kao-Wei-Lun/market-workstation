<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="總覽"
      description="快速查看市場廣度、候選名單、群組強弱、日報與近期研究訊號。"
    >
      <div class="page-actions">
        <RouterLink
          v-if="selectedWatchlistId"
          class="pill link-pill"
          :to="{ name: 'watchlists', query: { watchlistId: selectedWatchlistId, tradeDate: selectedTradeDate || undefined } }"
        >
          前往清單頁
        </RouterLink>
        <RouterLink
          v-if="selectedTag"
          class="pill link-pill"
          :to="{ name: 'groups', query: { tag: selectedTag, tradeDate: selectedTradeDate || undefined } }"
        >
          前往群組頁
        </RouterLink>
      </div>
    </PageHeader>

    <FilterBar
      title="總覽篩選"
      description="調整儀表板查詢使用的交易日期、觀察清單與標籤範圍。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="overview-trade-date">交易日期</label>
          <input id="overview-trade-date" v-model="selectedTradeDate" type="date" />
        </div>
        <div class="field-group">
          <label for="overview-watchlist">觀察清單</label>
          <select id="overview-watchlist" v-model="selectedWatchlistId">
            <option value="">不限</option>
            <option v-for="watchlist in watchlistsStore.items" :key="watchlist.id" :value="String(watchlist.id)">
              {{ watchlist.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="overview-tag">標籤</label>
          <input id="overview-tag" v-model="selectedTag" placeholder="semiconductor / ai / etf" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadOverview">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="總覽資料狀態"
      :as-of-date="overview?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(overview?.meta.generated_at)"
      :item-count="overview?.meta.item_count"
      hint="可同時用日期、清單與標籤縮小總覽範圍。"
      demo-hint="若畫面仍為空，請執行 make demo-data 產生本機示範資料。"
      :show-refresh="true"
      @refresh="loadOverview"
    />

    <LoadingState v-if="isLoading" message="正在載入總覽儀表板..." />
    <ErrorState
      v-else-if="errorMessage"
      title="總覽載入失敗"
      message="無法從後端載入總覽儀表板資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="overview?.meta.is_empty"
      title="尚無總覽資料"
      message="後端目前還沒有可供顯示的市場資料。執行 make demo-data 後即可看到總覽卡片、報表、候選、衍生性商品與回測內容。"
    />
    <template v-else-if="overview">
      <SummaryCardGrid :cards="overview.summary_cards" />

      <DetailPanel
        title="本次重點"
        description="依目前範圍整理出的高層觀察重點。"
      >
        <template #header>
          <span class="pill info">資料日期 {{ overview.meta.as_of_date ?? "無資料" }}</span>
        </template>
        <ul class="highlights">
          <li v-for="item in overview.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <MetricGrid :metrics="marketMetrics" />
        <MiniBarChart
          title="市場廣度快照"
          description="顯示最新市場摘要中的上漲、下跌與持平家數。"
          :points="breadthChartPoints"
          empty-message="目前沒有市場廣度資料。"
        />
        <MiniBarChart
          title="候選分數梯隊"
          description="顯示最新候選批次中的高分標的。"
          :points="candidateChartPoints"
          empty-message="目前沒有候選分數資料。"
        />
      </div>

      <div class="page-section-grid">
        <SortableTableSection
          title="高分候選名單"
          description="顯示最新候選批次中排名最高的隔日觀察標的。"
          :columns="candidateColumns"
          :rows="candidateRows"
          default-sort-by="score"
          default-sort-direction="desc"
          empty-message="目前沒有候選項目。"
        />
        <SortableTableSection
          title="近期報表"
          description="顯示目前查詢日期下最近保存的報表內容。"
          :columns="reportColumns"
          :rows="reportRows"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="目前沒有報表資料。"
        />
        <SortableTableSection
          title="近期回測"
          description="顯示儀表板可用的近期回測批次。"
          :columns="backtestColumns"
          :rows="backtestRows"
          default-sort-by="return_pct"
          default-sort-direction="desc"
          empty-message="目前沒有回測資料。"
        />
      </div>

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
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { fetchOverview } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import { useWatchlistsStore } from "@/stores/watchlists";
import type { DashboardOverviewRead } from "@/types/dashboard";
import { formatDate, formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const overview = ref<DashboardOverviewRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedTag = ref("semiconductor");
const selectedWatchlistId = ref("");
const selectedTradeDate = ref("");
const watchlistsStore = useWatchlistsStore();
const route = useRoute();
const router = useRouter();

const candidateColumns = [
  { key: "rank", label: "排名" },
  { key: "symbol", label: "代號" },
  { key: "score", label: "分數" },
  { key: "reasons", label: "原因" },
];

const reportColumns = [
  { key: "date", label: "日期" },
  { key: "type", label: "類型" },
  { key: "title", label: "標題" },
];

const backtestColumns = [
  { key: "run_id", label: "批次" },
  { key: "return_pct", label: "報酬率 %" },
  { key: "trades", label: "交易筆數" },
  { key: "status", label: "狀態" },
];

const candidateRows = computed(() =>
  overview.value?.data.candidate_summary?.top_items.map((item) => ({
    rank: item.rank,
    symbol: makeLinkedCell(item.symbol, {
      name: "candidates",
      query: {
        run: String(overview.value?.data.candidate_summary?.run.id ?? ""),
        search: item.symbol,
        candidateDate: item.candidate_date,
      },
    }),
    score: Number(item.score),
    reasons: formatList(item.candidate_reasons, "無理由說明"),
  })) ?? [],
);

const reportRows = computed(() =>
  overview.value?.data.report_summary?.reports.map((report) => ({
    date: formatDate(report.report_date),
    type: report.report_type,
    title: makeLinkedCell(report.title, {
      name: "reports",
      query: {
        reportDate: report.report_date,
        reportType: report.report_type,
      },
    }),
  })) ?? [],
);

const backtestRows = computed(() =>
  overview.value?.data.backtest_summary?.recent_runs.map((run) => ({
    run_id: makeLinkedCell(`#${run.id}`, { name: "backtests", query: { run: String(run.id) } }),
    return_pct: Number(run.total_return_pct),
    trades: run.total_trades,
    status: run.status,
  })) ?? [],
);

const marketMetrics = computed(() => {
  const marketSnapshot = overview.value?.data.market_snapshot;
  if (!marketSnapshot) {
    return [];
  }
  return [
    { label: "追蹤標的數", value: formatNumber(marketSnapshot.instrument_count), hint: "已有日線資料" },
    { label: "平均漲跌", value: formatPercent(marketSnapshot.average_close_change_pct), hint: "收盤對收盤" },
    { label: "站上 SMA20", value: formatPercent(marketSnapshot.percentage_above_sma20), hint: "廣度強弱" },
    {
      label: "高分候選數",
      value: formatNumber(overview.value?.data.candidate_summary?.top_items.length ?? 0),
      hint: "已排序標的",
    },
  ];
});

const breadthChartPoints = computed(() => {
  const marketSnapshot = overview.value?.data.market_snapshot;
  if (!marketSnapshot) {
    return [];
  }
  return [
    { label: "上漲", value: marketSnapshot.advancers, tone: "positive" as const },
    { label: "下跌", value: marketSnapshot.decliners, tone: "negative" as const },
    { label: "持平", value: marketSnapshot.unchanged, tone: "neutral" as const },
  ];
});

const candidateChartPoints = computed(() =>
  overview.value?.data.candidate_summary?.top_items.map((item) => ({
    label: item.symbol,
    value: Number(item.score),
    tone: "info" as const,
  })) ?? [],
);

async function loadOverview(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    overview.value = await fetchOverview({
      tradeDate: selectedTradeDate.value || undefined,
      watchlistId: selectedWatchlistId.value ? Number(selectedWatchlistId.value) : undefined,
      tag: selectedTag.value || undefined,
      topN: 5,
    });
    await router.replace({
      query: {
        tradeDate: selectedTradeDate.value || undefined,
        watchlistId: selectedWatchlistId.value || undefined,
        tag: selectedTag.value || undefined,
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
  selectedTradeDate.value = typeof route.query.tradeDate === "string" ? route.query.tradeDate : "";
  selectedTag.value = typeof route.query.tag === "string" ? route.query.tag : "semiconductor";
  selectedWatchlistId.value = typeof route.query.watchlistId === "string" ? route.query.watchlistId : "";
  if (!selectedWatchlistId.value && watchlistsStore.items[0]) {
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

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.link-pill {
  text-decoration: none;
}
</style>
