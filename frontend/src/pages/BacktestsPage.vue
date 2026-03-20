<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Backtests"
      description="Recent backtest runs, key metrics, and the latest trade list for local research review."
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
      </div>
    </PageHeader>

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
      <section class="panel">
        <div class="panel-header">
          <SectionHeader title="Backtest Highlights" description="Recent research outcomes surfaced through the dashboard." />
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>
      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <TableSection
          title="Recent Runs"
          description="Most recent backtest runs persisted in the backend."
          :columns="runColumns"
          :rows="runRows"
          empty-message="No backtest runs available."
        />
        <TableSection
          title="Selected Run Trades"
          description="Trade list for the latest available backtest run."
          :columns="tradeColumns"
          :rows="tradeRows"
          empty-message="No trades available for the selected run."
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchBacktestRuns, fetchBacktestRunTrades } from "@/api/backtests";
import { fetchBacktestsDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import type { BacktestRunRead, BacktestTradeRead, BacktestsDashboardRead } from "@/types/dashboard";
import { formatDate, formatNumber, formatPercent } from "@/utils/formatters";

const dashboard = ref<BacktestsDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const runs = ref<BacktestRunRead[]>([]);
const trades = ref<BacktestTradeRead[]>([]);
const selectedRunId = ref<number | null>(null);
const selectedRunIdString = computed({
  get: () => (selectedRunId.value ? String(selectedRunId.value) : ""),
  set: (value: string) => {
    selectedRunId.value = value ? Number(value) : null;
  },
});

const runColumns = [
  { key: "run_id", label: "Run" },
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
    run_id: `#${run.id}${run.id === selectedRunId.value ? " (selected)" : ""}`,
    return_pct: formatPercent(run.total_return_pct),
    trades: formatNumber(run.total_trades),
    status: run.status,
  })),
);

const tradeRows = computed(() =>
  trades.value.map((trade) => ({
    instrument_id: trade.instrument_id,
    entry_date: formatDate(trade.entry_date),
    exit_date: formatDate(trade.exit_date),
    net_pnl: formatNumber(trade.net_pnl),
    reason: trade.exit_reason,
  })),
);

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
    selectedRunId.value = dashboardResponse.data?.latest_run?.id ?? runsResponse[0]?.id ?? null;
    await loadSelectedRunTrades();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedRunTrades(): Promise<void> {
  trades.value = selectedRunId.value ? await fetchBacktestRunTrades(selectedRunId.value) : [];
}

onMounted(loadBacktests);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
}
</style>
