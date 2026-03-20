<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="總覽"
      description="作為每日工作入口，快速掌握資料新鮮度、候選、報表、觀察清單、族群、法人與回測摘要。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
          打開報表
        </RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'candidates', query: { candidateDate: selectedTradeDate || undefined } }">
          打開候選
        </RouterLink>
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
        <RouterLink class="pill link-pill" :to="{ name: 'operations' }">
          任務中心
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
      hint="總覽會同時整合市場摘要、候選、報表、回測與系統新鮮度。"
      :demo-hint="workspaceReadinessHint"
      :show-refresh="true"
      @refresh="loadOverview"
    />

    <LoadingState v-if="isLoading" message="正在整理今日工作站總覽..." />
    <ErrorState
      v-else-if="errorMessage"
      title="總覽載入失敗"
      message="無法從後端載入總覽與系統摘要資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="overview?.meta.is_empty"
      title="尚無總覽資料"
      message="後端目前還沒有可供顯示的市場資料。執行 make demo-data 後即可看到總覽卡片、報表、候選、衍生性商品與回測內容。"
    />
    <template v-else-if="overview">
      <SummaryCardGrid :cards="overview.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="今日工作入口" description="先確認資料新鮮度與準備狀態，再決定往哪個研究頁面深入。">
          <template #header>
            <div class="detail-actions">
              <RouterLink class="detail-link" :to="{ name: 'coverage' }">檢查資料覆蓋</RouterLink>
              <RouterLink class="detail-link" :to="{ name: 'operations' }">打開任務中心</RouterLink>
              <RouterLink class="detail-link" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
                閱讀當日報表
              </RouterLink>
            </div>
          </template>
          <MetricGrid :metrics="workspaceMetrics" />
        </DetailPanel>
        <DetailPanel
          title="資料與產出新鮮度"
          description="顯示最新資料日期、最近成功匯入、最近報表生成與目前就緒資料集數。"
        >
          <MetricGrid :metrics="freshnessMetrics" />
        </DetailPanel>
      </div>

      <DetailPanel
        title="本次重點"
        description="依目前範圍整理出的高層觀察重點與今日優先查看項目。"
      >
        <template #header>
          <div class="detail-actions">
            <span class="pill info">資料日期 {{ overview.meta.as_of_date ?? "無資料" }}</span>
            <span class="pill">生成時間 {{ formatDateTime(overview.meta.generated_at) }}</span>
          </div>
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
        <DetailPanel
          title="候選摘要"
          description="快速檢查當前候選批次的規模、最高分與前往候選頁的入口。"
        >
          <template #header>
            <RouterLink class="detail-link" :to="{ name: 'candidates', query: { candidateDate: selectedTradeDate || undefined } }">
              查看候選頁
            </RouterLink>
          </template>
          <MetricGrid :metrics="candidateSummaryMetrics" />
        </DetailPanel>
        <DetailPanel
          title="報表摘要"
          description="快速檢查最近報表日期、類型數與報表頁入口。"
        >
          <template #header>
            <RouterLink class="detail-link" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
              查看報表頁
            </RouterLink>
          </template>
          <MetricGrid :metrics="reportSummaryMetrics" />
        </DetailPanel>
        <DetailPanel
          title="回測摘要"
          description="快速檢查最近回測批次、報酬與交易筆數。"
        >
          <template #header>
            <RouterLink class="detail-link" :to="{ name: 'backtests' }">查看回測頁</RouterLink>
          </template>
          <MetricGrid :metrics="backtestSummaryMetrics" />
        </DetailPanel>
      </div>

      <div class="page-section-grid">
        <DetailPanel
          title="觀察清單摘要"
          description="顯示目前選定觀察清單的成員、平均漲跌與 scanner 命中。"
        >
          <template #header>
            <RouterLink
              v-if="selectedWatchlistId"
              class="detail-link"
              :to="{ name: 'watchlists', query: { watchlistId: selectedWatchlistId, tradeDate: selectedTradeDate || undefined } }"
            >
              查看清單頁
            </RouterLink>
          </template>
          <MetricGrid :metrics="watchlistSummaryMetrics" />
        </DetailPanel>
        <DetailPanel
          title="族群摘要"
          description="顯示目前選定標籤群組的成員、平均漲跌與 scanner 命中。"
        >
          <template #header>
            <RouterLink
              v-if="selectedTag"
              class="detail-link"
              :to="{ name: 'groups', query: { tag: selectedTag, tradeDate: selectedTradeDate || undefined } }"
            >
              查看群組頁
            </RouterLink>
          </template>
          <MetricGrid :metrics="groupSummaryMetrics" />
        </DetailPanel>
        <DetailPanel
          title="法人／衍生性商品摘要"
          description="顯示最新偏向 regime、異常數與重點，方便決定是否先看衍生性商品頁。"
        >
          <template #header>
            <RouterLink class="detail-link" :to="{ name: 'derivatives' }">查看衍生性商品頁</RouterLink>
          </template>
          <MetricGrid :metrics="derivativesSummaryMetrics" />
        </DetailPanel>
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
import { fetchSystemStatus } from "@/api/system";
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
import type { SystemStatusRead } from "@/types/system";
import { formatDate, formatDateTime, formatList, formatNumber, formatPercent } from "@/utils/formatters";
import { makeLinkedCell } from "@/utils/presentation";

const overview = ref<DashboardOverviewRead | null>(null);
const systemStatus = ref<SystemStatusRead | null>(null);
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

const latestSuccessfulJob = computed(() =>
  systemStatus.value?.data.recent_jobs.find((job) => job.status === "success") ?? null,
);

const latestReport = computed(() => overview.value?.data.report_summary?.reports[0] ?? null);

const readyDatasetCount = computed(
  () => systemStatus.value?.data.datasets.filter((dataset) => dataset.status === "ready").length ?? 0,
);

const workspaceReadinessHint = computed(() => {
  if ((systemStatus.value?.data.recent_jobs.length ?? 0) === 0) {
    return "若畫面仍為空，請執行 make demo-data 產生本機示範資料。";
  }
  return `目前已有 ${readyDatasetCount.value}/${systemStatus.value?.data.datasets.length ?? 0} 個主要資料集就緒。`;
});

const workspaceMetrics = computed(() => [
  { label: "資料日期", value: formatDate(overview.value?.meta.as_of_date ?? null), hint: "目前總覽基準日" },
  { label: "生成時間", value: formatDateTime(overview.value?.meta.generated_at ?? null), hint: "總覽 API 生成時間" },
  { label: "就緒資料集", value: `${readyDatasetCount.value}/${systemStatus.value?.data.datasets.length ?? 0}`, hint: "資料可見性" },
  { label: "最近成功工作", value: formatDateTime(latestSuccessfulJob.value?.finished_at ?? latestSuccessfulJob.value?.started_at ?? null), hint: latestSuccessfulJob.value?.job_type ?? "尚無工作" },
]);

const freshnessMetrics = computed(() => [
  {
    label: "最新資料日期",
    value: formatDate(systemStatus.value?.data.datasets.find((dataset) => dataset.dataset_key === "daily_bars")?.latest_date ?? null),
    hint: "daily bars",
  },
  {
    label: "最近 ETL 成功",
    value: formatDateTime(latestSuccessfulJob.value?.finished_at ?? latestSuccessfulJob.value?.started_at ?? null),
    hint: latestSuccessfulJob.value?.source_route ?? "尚無成功工作",
  },
  {
    label: "最近報表生成",
    value: formatDateTime(latestReport.value?.created_at ?? null),
    hint: latestReport.value?.report_type ?? "尚無報表",
  },
  {
    label: "報表資料日期",
    value: formatDate(latestReport.value?.report_date ?? null),
    hint: "最近報表基準日",
  },
]);

const candidateSummaryMetrics = computed(() => {
  const summary = overview.value?.data.candidate_summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "批次編號", value: `#${summary.run.id}`, hint: "目前候選 run" },
    { label: "候選總數", value: formatNumber(summary.run.total_candidates), hint: "同日批次結果" },
    { label: "最高分", value: formatNumber(summary.top_items[0]?.score ?? null), hint: summary.top_items[0]?.symbol ?? "無資料" },
    { label: "資料日期", value: formatDate(summary.run.candidate_date), hint: "候選基準日" },
  ];
});

const reportSummaryMetrics = computed(() => {
  const reports = overview.value?.data.report_summary?.reports ?? [];
  return [
    { label: "最近報表數", value: formatNumber(reports.length), hint: "目前列表可見" },
    { label: "最新報表日期", value: formatDate(reports[0]?.report_date ?? null), hint: "最近資料日" },
    { label: "最新生成時間", value: formatDateTime(reports[0]?.created_at ?? null), hint: reports[0]?.report_type ?? "尚無資料" },
    { label: "類型數", value: formatNumber(new Set(reports.map((item) => item.report_type)).size), hint: "不同 report_type" },
  ];
});

const backtestSummaryMetrics = computed(() => {
  const summary = overview.value?.data.backtest_summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "最近回測", value: summary.latest_run ? `#${summary.latest_run.id}` : "無資料", hint: "最近完成批次" },
    { label: "批次數", value: formatNumber(summary.recent_runs.length), hint: "目前列表可見" },
    { label: "最近報酬", value: formatPercent(summary.latest_run?.total_return_pct ?? null), hint: "latest run" },
    { label: "最近交易筆數", value: formatNumber(summary.latest_run?.total_trades ?? null), hint: "latest run" },
  ];
});

const watchlistSummaryMetrics = computed(() => {
  const summary = overview.value?.data.watchlist_summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "觀察清單", value: summary.watchlist.name, hint: "目前焦點清單" },
    { label: "成員數", value: formatNumber(summary.summary.member_count), hint: "清單規模" },
    { label: "平均漲跌", value: formatPercent(summary.summary.average_close_change_pct), hint: "日內變化" },
    { label: "掃描旗標", value: formatNumber(summary.scanner?.flagged_instruments.length ?? 0), hint: "命中數" },
  ];
});

const groupSummaryMetrics = computed(() => {
  const summary = overview.value?.data.group_summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "標籤群組", value: summary.tag, hint: "目前焦點群組" },
    { label: "成員數", value: formatNumber(summary.summary.member_count), hint: "群組規模" },
    { label: "平均漲跌", value: formatPercent(summary.summary.average_close_change_pct), hint: "日內變化" },
    { label: "掃描旗標", value: formatNumber(summary.scanner?.flagged_instruments.length ?? 0), hint: "命中數" },
  ];
});

const derivativesSummaryMetrics = computed(() => {
  const summary = overview.value?.data.derivatives_summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "資料日期", value: formatDate(summary.trade_date), hint: "法人摘要基準日" },
    { label: "整體偏向", value: summary.overall_regime, hint: "regime" },
    { label: "異常數", value: formatNumber(summary.anomaly_count), hint: "需複核" },
    { label: "平均 bias", value: formatNumber(summary.average_bias_score), hint: "偏向分數" },
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
    const [overviewResponse, systemStatusResponse] = await Promise.all([
      fetchOverview({
        tradeDate: selectedTradeDate.value || undefined,
        watchlistId: selectedWatchlistId.value ? Number(selectedWatchlistId.value) : undefined,
        tag: selectedTag.value || undefined,
        topN: 5,
      }),
      fetchSystemStatus({ jobLimit: 10, workerStaleMinutes: 30 }),
    ]);
    overview.value = overviewResponse;
    systemStatus.value = systemStatusResponse;
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

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.detail-link {
  color: var(--accent);
  text-decoration: none;
}

.detail-link:hover {
  text-decoration: underline;
}
</style>
