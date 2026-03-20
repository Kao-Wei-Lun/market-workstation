<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Backtests"
      description="Recent backtest runs, key metrics, and the latest trade list for local research review."
    />

    <FilterBar
      title="Backtest Explorer"
      description="Choose a persisted run and review returns, metrics, and trades."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="backtest-run">Run</label>
          <select id="backtest-run" v-model="selectedRunIdString" @change="loadSelectedRunTrades">
            <option value="">Latest</option>
            <option v-for="run in runs" :key="run.id" :value="String(run.id)">
              #{{ run.id }} {{ formatPercent(run.total_return_pct) }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadBacktests">Refresh</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="Backtest Data Status"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="Backtests combine run-level metrics, trade lists, and dashboard highlights."
      demo-hint="Run make demo-data if no backtests are visible."
      :show-refresh="true"
      @refresh="loadBacktests"
    />

    <LoadingState v-if="isLoading" message="Loading backtests dashboard..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Backtest request failed"
      message="Recent runs or trades could not be loaded."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No backtests available"
      message="The backend is healthy but has no backtest runs yet. Run make demo-data to generate a repeatable local demo backtest with trades."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="Selected Run" description="Focused metrics for the currently selected backtest run.">
          <MetricGrid :metrics="selectedRunMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="Return Comparison"
          description="Recent backtest run returns for quick comparison."
          :points="runChartPoints"
          empty-message="No recent run returns available."
        />
      </div>

      <DetailPanel title="Backtest Highlights" description="Recent research outcomes surfaced through the dashboard.">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="Recent Runs"
          description="Most recent backtest runs persisted in the backend."
          :columns="runColumns"
          :rows="runRows"
          row-key="run_key"
          :selected-row-key="selectedRunRowKey"
          :interactive-rows="true"
          @row-select="handleRunRowSelect"
          default-sort-by="return_pct"
          default-sort-direction="desc"
          empty-message="No backtest runs available."
        />
        <SortableTableSection
          title="Selected Run Trades"
          description="Trade list for the latest available backtest run."
          :columns="tradeColumns"
          :rows="tradeRows"
          row-key="trade_key"
          :selected-row-key="selectedTradeRowKey"
          :interactive-rows="true"
          @row-select="handleTradeRowSelect"
          default-sort-by="entry_date"
          default-sort-direction="asc"
          empty-message="No trades available for the selected run."
        />
      </div>

      <DetailPanel v-if="selectedTrade" title="Selected Trade Detail" description="Trade-level exit, holding period, and cost context.">
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
  { key: "run_id", label: "Run" },
  { key: "created_at", label: "Created" },
  { key: "return_pct", label: "Return %" },
  { key: "trades", label: "Trades" },
  { key: "status", label: "Status" },
];

const tradeColumns = [
  { key: "instrument_id", label: "Instrument" },
  { key: "entry_date", label: "Entry" },
  { key: "exit_date", label: "Exit" },
  { key: "net_pnl", label: "Net PnL" },
  { key: "reason", label: "Exit Reason" },
];

const runRows = computed(() =>
  runs.value.map((run) => ({
    run_key: run.id,
    run_id: `#${run.id}${run.id === selectedRunId.value ? " (selected)" : ""}`,
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
    { label: "Total Return", value: formatPercent(selectedRun.value.total_return_pct), hint: "net run return" },
    { label: "Win Rate", value: formatPercent(selectedRun.value.win_rate), hint: "winning trades" },
    { label: "Sharpe", value: metricNumber(selectedRunMetricsJson.value.sharpe_ratio), hint: "from run metrics" },
    { label: "Score", value: metricNumber(selectedRunMetricsJson.value.score), hint: "ranking metric" },
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
    { label: "Instrument", value: formatNumber(selectedTrade.value.instrument_id), hint: "instrument id" },
    { label: "Holding Days", value: formatNumber(selectedTrade.value.holding_period_days), hint: "trade duration" },
    { label: "Net PnL", value: formatNumber(selectedTrade.value.net_pnl), hint: "after costs" },
    { label: "Exit Reason", value: selectedTrade.value.exit_reason, hint: "engine exit condition" },
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
