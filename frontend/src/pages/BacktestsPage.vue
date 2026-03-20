<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="回測"
      description="查看近期回測批次、核心指標與交易明細，方便本機研究使用。"
    />

    <FilterBar
      title="回測探索"
      description="切換已保存回測批次，查看報酬、指標與交易內容。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="backtest-run">批次</label>
          <select id="backtest-run" v-model="selectedRunIdString" @change="loadSelectedRunTrades">
            <option value="">最新批次</option>
            <option v-for="run in runs" :key="run.id" :value="String(run.id)">
              #{{ run.id }} {{ formatPercent(run.total_return_pct) }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadBacktests">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="回測資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="回測頁整合批次指標、交易清單與儀表板重點。"
      demo-hint="若尚無回測資料，請執行 make demo-data 產生示範回測。"
      :show-refresh="true"
      @refresh="loadBacktests"
    />

    <LoadingState v-if="isLoading" message="正在載入回測資料..." />
    <ErrorState
      v-else-if="errorMessage"
      title="回測載入失敗"
      message="無法載入近期批次或交易明細。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無回測資料"
      message="後端目前沒有任何回測批次。執行 make demo-data 後即可產生可重複的本機回測與交易資料。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="目前回測批次" description="顯示目前選定回測批次的核心指標。">
          <MetricGrid :metrics="selectedRunMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="報酬比較"
          description="快速比較近期回測批次的報酬表現。"
          :points="runChartPoints"
          empty-message="目前沒有近期回測報酬資料。"
        />
      </div>

      <DetailPanel title="回測重點" description="整理近期研究結果中最值得關注的內容。">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="近期批次"
          description="顯示後端保存的近期回測批次。"
          :columns="runColumns"
          :rows="runRows"
          row-key="run_key"
          :selected-row-key="selectedRunRowKey"
          :interactive-rows="true"
          @row-select="handleRunRowSelect"
          default-sort-by="return_pct"
          default-sort-direction="desc"
          empty-message="目前沒有回測批次。"
        />
        <SortableTableSection
          title="目前批次交易"
          description="顯示目前選定回測批次的交易明細。"
          :columns="tradeColumns"
          :rows="tradeRows"
          row-key="trade_key"
          :selected-row-key="selectedTradeRowKey"
          :interactive-rows="true"
          @row-select="handleTradeRowSelect"
          default-sort-by="entry_date"
          default-sort-direction="asc"
          empty-message="目前批次沒有交易資料。"
        />
      </div>

      <DetailPanel v-if="selectedTrade" title="交易明細" description="顯示單筆交易的出場、持有天數與成本資訊。">
        <MetricGrid :metrics="selectedTradeMetrics" />
      </DetailPanel>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchBacktestRuns, fetchBacktestRunTrades } from "@/api/backtests";
import { fetchBacktestsDashboard } from "@/api/dashboard";
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
import type { BacktestRunRead, BacktestTradeRead, BacktestsDashboardRead } from "@/types/dashboard";
import type { TableRow } from "@/utils/presentation";
import { formatDate, formatDateTime, formatNumber, formatPercent } from "@/utils/formatters";

const dashboard = ref<BacktestsDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const runs = ref<BacktestRunRead[]>([]);
const trades = ref<BacktestTradeRead[]>([]);
const selectedRunId = ref<number | null>(null);
const selectedTradeId = ref<number | null>(null);
const route = useRoute();
const router = useRouter();
const selectedRunIdString = computed({
  get: () => (selectedRunId.value ? String(selectedRunId.value) : ""),
  set: (value: string) => {
    selectedRunId.value = value ? Number(value) : null;
  },
});

const selectedRun = computed(() => runs.value.find((run) => run.id === selectedRunId.value) ?? null);
const selectedTrade = computed(() => trades.value.find((trade) => trade.id === selectedTradeId.value) ?? null);
const selectedRunMetricsJson = computed<Record<string, unknown>>(
  () => (selectedRun.value?.metrics_json as Record<string, unknown> | undefined) ?? {},
);

function metricNumber(value: unknown): string {
  return formatNumber(typeof value === "string" || typeof value === "number" ? value : null);
}

const runColumns = [
  { key: "run_id", label: "批次" },
  { key: "created_at", label: "建立時間" },
  { key: "return_pct", label: "報酬率 %" },
  { key: "trades", label: "交易筆數" },
  { key: "status", label: "狀態" },
];

const tradeColumns = [
  { key: "instrument_id", label: "標的" },
  { key: "entry_date", label: "進場" },
  { key: "exit_date", label: "出場" },
  { key: "net_pnl", label: "淨損益" },
  { key: "reason", label: "出場原因" },
];

const runRows = computed(() =>
  runs.value.map((run) => ({
    run_key: run.id,
    run_id: `#${run.id}${run.id === selectedRunId.value ? "（目前）" : ""}`,
    created_at: formatDateTime(run.created_at),
    return_pct: Number(run.total_return_pct),
    trades: run.total_trades,
    status: run.status,
  })),
);

const tradeRows = computed(() =>
  trades.value.map((trade) => ({
    trade_key: trade.id,
    instrument_id: trade.instrument_id,
    entry_date: formatDate(trade.entry_date),
    exit_date: formatDate(trade.exit_date),
    net_pnl: Number(trade.net_pnl),
    reason: trade.exit_reason,
  })),
);

const selectedRunRowKey = computed(() => (selectedRunId.value ? String(selectedRunId.value) : null));
const selectedTradeRowKey = computed(() => (selectedTradeId.value ? String(selectedTradeId.value) : null));

const selectedRunMetrics = computed(() => {
  if (!selectedRun.value) {
    return [];
  }
  return [
    { label: "總報酬", value: formatPercent(selectedRun.value.total_return_pct), hint: "淨報酬率" },
    { label: "勝率", value: formatPercent(selectedRun.value.win_rate), hint: "獲利交易比例" },
    { label: "Sharpe", value: metricNumber(selectedRunMetricsJson.value.sharpe_ratio), hint: "來自回測指標" },
    { label: "評分", value: metricNumber(selectedRunMetricsJson.value.score), hint: "排序分數" },
  ];
});

const runChartPoints = computed(() =>
  runs.value.slice(0, 6).map((run) => ({
    label: `#${run.id}`,
    value: Number(run.total_return_pct),
    tone: Number(run.total_return_pct) >= 0 ? ("positive" as const) : ("negative" as const),
  })),
);

const selectedTradeMetrics = computed(() => {
  if (!selectedTrade.value) {
    return [];
  }
  return [
    { label: "標的", value: formatNumber(selectedTrade.value.instrument_id), hint: "標的 ID" },
    { label: "持有天數", value: formatNumber(selectedTrade.value.holding_period_days), hint: "交易持有期間" },
    { label: "淨損益", value: formatNumber(selectedTrade.value.net_pnl), hint: "成本後損益" },
    { label: "出場原因", value: selectedTrade.value.exit_reason, hint: "回測引擎條件" },
  ];
});

function handleRunRowSelect(row: TableRow): void {
  selectedRunId.value = Number(row.run_key);
  void loadSelectedRunTrades();
}

function handleTradeRowSelect(row: TableRow): void {
  selectedTradeId.value = Number(row.trade_key);
}

async function loadBacktests(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [dashboardResponse, runsResponse] = await Promise.all([
      fetchBacktestsDashboard(5),
      fetchBacktestRuns(10),
    ]);
    dashboard.value = dashboardResponse;
    runs.value = runsResponse;
    selectedRunId.value = selectedRunId.value ?? dashboardResponse.data?.latest_run?.id ?? runsResponse[0]?.id ?? null;
    await loadSelectedRunTrades();
    await router.replace({
      query: {
        run: selectedRunId.value ? String(selectedRunId.value) : undefined,
      },
    });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedRunTrades(): Promise<void> {
  trades.value = selectedRunId.value ? await fetchBacktestRunTrades(selectedRunId.value) : [];
  selectedTradeId.value = trades.value[0]?.id ?? null;
}

onMounted(() => {
  selectedRunId.value = typeof route.query.run === "string" ? Number(route.query.run) : null;
  return loadBacktests();
});
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
}
</style>
