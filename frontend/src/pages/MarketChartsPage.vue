<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="圖表"
      title="大盤與法人流圖"
      description="查看台灣大盤日線 K 線圖，並疊合外資期貨／選擇權流向 foundation。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'derivatives' }">查看衍生性商品摘要</RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'reports' }">查看每日報表</RouterLink>
      </div>
    </PageHeader>

    <FilterBar title="市場圖表篩選" description="切換指數、日期區間、技術指標與畫線工具。">
      <div class="form-inline">
        <div class="field-group wide-field">
          <label for="market-chart-symbol">指數</label>
          <select id="market-chart-symbol" v-model="selectedSymbol" @change="loadChart">
            <option v-for="instrument in instruments" :key="instrument.symbol" :value="instrument.symbol">
              {{ instrument.symbol }} / {{ instrument.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="market-date-from">起始</label>
          <input id="market-date-from" v-model="dateFrom" type="date" />
        </div>
        <div class="field-group">
          <label for="market-date-to">結束</label>
          <input id="market-date-to" v-model="dateTo" type="date" />
        </div>
        <div class="field-group">
          <label for="market-tool">畫線工具</label>
          <select id="market-tool" v-model="activeTool">
            <option value="none">不啟用</option>
            <option value="trend_line">趨勢線</option>
            <option value="horizontal_line">水平線</option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadChart">重新整理</button>
        </div>
      </div>
      <div class="toolbar-row">
        <div class="quick-range">
          <button type="button" class="secondary-button" @click="applyQuickRange(90)">近 3 個月</button>
          <button type="button" class="secondary-button" @click="applyQuickRange(180)">近 6 個月</button>
          <button type="button" class="secondary-button" @click="applyQuickRange(365)">近 1 年</button>
        </div>
        <div class="indicator-toggles">
          <label v-for="indicator in availableIndicators" :key="indicator" class="toggle-pill">
            <input v-model="selectedIndicators" type="checkbox" :value="indicator" />
            {{ indicator.toUpperCase() }}
          </label>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="大盤圖表狀態"
      :as-of-date="chartData?.instrument.latest_data_date ?? null"
      :generated-at="null"
      :item-count="chartData?.candles.length"
      hint="目前以台灣指數日線為主，並提供外資期貨／選擇權流向合成 foundation。"
      demo-hint="若無資料，請先執行 make demo-data 或載入相關 universe。"
      :show-refresh="true"
      @refresh="loadChart"
    />

    <LoadingState v-if="isLoading" message="正在載入大盤與法人流圖..." />
    <ErrorState
      v-else-if="errorMessage"
      title="市場圖表載入失敗"
      message="無法載入大盤 K 線或法人流向資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="!chartData || !chartData.candles.length"
      title="尚無市場圖表資料"
      message="目前選定指數尚未有可顯示的日線資料。"
    />
    <template v-else>
      <div class="page-section-grid">
        <DetailPanel title="市場摘要" description="整理目前指數日線與法人流向 foundation 的核心資訊。">
          <MetricGrid :metrics="marketMetrics" />
        </DetailPanel>
        <ChartAnnotationsPanel
          :annotations="chartData.annotations"
          description="大盤頁的畫線與個股頁分開保存，適合保留長期觀察區間。"
          @remove="handleRemoveAnnotation"
          @clear="handleClearAnnotations"
        />
      </div>

      <CandlestickChart
        title="大盤日線 K 線圖"
        description="使用 index 日線與已保存的技術指標作為 overlay。"
        :candles="chartData.candles"
        :indicators="visibleIndicators"
        :annotations="chartData.annotations"
        :active-tool="activeTool"
        :draft-trend-start="trendDraft"
        empty-message="目前沒有指數日線資料。"
        @plot-click="handlePlotClick"
      />

      <InstitutionalFlowChart
        title="外資期貨／選擇權流向"
        description="以大盤日期軸對齊外資期貨、選擇權淨未平倉與 bias score。"
        :flow-points="flowData?.flow_points ?? []"
        empty-message="目前沒有可用的法人流向資料。"
      />

      <DetailPanel title="法人流向重點" description="這個 foundation 先支援大盤＋外資期權流向，現貨流向後續再補。">
        <ul class="highlights">
          <li v-for="item in (flowData?.summary_highlights ?? [])" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { clearChartAnnotations, createChartAnnotation, deleteChartAnnotation, fetchChartData, fetchChartInstruments, fetchInstitutionalFlowChart } from "@/api/charts";
import { normalizeApiError } from "@/api/http";
import CandlestickChart from "@/components/CandlestickChart.vue";
import ChartAnnotationsPanel from "@/components/ChartAnnotationsPanel.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import InstitutionalFlowChart from "@/components/InstitutionalFlowChart.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import PageHeader from "@/components/PageHeader.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import type { ChartDataRead, ChartIndicatorSeriesRead, ChartInstrumentRead, InstitutionalFlowChartRead } from "@/types/charts";
import type { ChartPlotClickPayload } from "@/utils/charts";
import { buildDateRange, formatFlowHighlight } from "@/utils/charts";
import { formatDate, formatNumber } from "@/utils/formatters";

const route = useRoute();
const router = useRouter();
const instruments = ref<ChartInstrumentRead[]>([]);
const chartData = ref<ChartDataRead | null>(null);
const flowData = ref<InstitutionalFlowChartRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedSymbol = ref("");
const dateFrom = ref("");
const dateTo = ref("");
const selectedIndicators = ref<string[]>(["sma", "ema"]);
const activeTool = ref("none");
const trendDraft = ref<ChartPlotClickPayload | null>(null);

const availableIndicators = ["sma", "ema", "bollinger", "supertrend"];

const visibleIndicators = computed<ChartIndicatorSeriesRead[]>(() =>
  (chartData.value?.indicators ?? []).filter((series) => selectedIndicators.value.includes(series.indicator_name)),
);

const marketMetrics = computed(() => {
  if (!chartData.value) {
    return [];
  }
  const latestFlowPoint = flowData.value?.flow_points.length ? flowData.value.flow_points[flowData.value.flow_points.length - 1] : null;
  return [
    { label: "指數", value: `${chartData.value.instrument.symbol} / ${chartData.value.instrument.name}`, hint: "大盤標的" },
    { label: "最新資料", value: formatDate(chartData.value.instrument.latest_data_date), hint: "日線日期" },
    { label: "K 線筆數", value: formatNumber(chartData.value.candles.length), hint: "載入筆數" },
    { label: "法人流向", value: formatFlowHighlight(latestFlowPoint), hint: "最新流向摘要" },
    { label: "畫線數量", value: formatNumber(chartData.value.annotations.length), hint: "本機持久化注記" },
  ];
});

async function loadInstrumentOptions(): Promise<void> {
  try {
    instruments.value = await fetchChartInstruments({
      market: "TW",
      assetType: "index",
      limit: 30,
    });
    if (!selectedSymbol.value && instruments.value.length) {
      const fromRoute = String(route.query.symbol ?? "");
      selectedSymbol.value = instruments.value.some((item) => item.symbol === fromRoute)
        ? fromRoute
        : (instruments.value.find((item) => item.symbol === "^TWII")?.symbol ?? instruments.value[0].symbol);
    }
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  }
}

async function loadChart(): Promise<void> {
  if (!selectedSymbol.value) {
    return;
  }
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [chartResponse, flowResponse] = await Promise.all([
      fetchChartData(selectedSymbol.value, {
        dateFrom: dateFrom.value || undefined,
        dateTo: dateTo.value || undefined,
        indicatorNames: selectedIndicators.value,
        viewKind: "index",
      }),
      fetchInstitutionalFlowChart(selectedSymbol.value, {
        dateFrom: dateFrom.value || undefined,
        dateTo: dateTo.value || undefined,
      }),
    ]);
    chartData.value = chartResponse;
    flowData.value = flowResponse;
    await router.replace({ name: "market-charts", query: { symbol: selectedSymbol.value } });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

function applyQuickRange(days: number): void {
  const range = buildDateRange(chartData.value?.instrument.latest_data_date, days);
  dateFrom.value = range.dateFrom;
  dateTo.value = range.dateTo;
  void loadChart();
}

async function handlePlotClick(payload: ChartPlotClickPayload): Promise<void> {
  if (!selectedSymbol.value || activeTool.value === "none") {
    return;
  }
  try {
    if (activeTool.value === "horizontal_line") {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "index",
        annotation_type: "horizontal_line",
        label: `水平 ${payload.price}`,
        payload_json: { price: payload.price, trade_date: payload.tradeDate },
      });
    } else if (!trendDraft.value) {
      trendDraft.value = payload;
      return;
    } else {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "index",
        annotation_type: "trend_line",
        label: `趨勢 ${trendDraft.value.tradeDate}`,
        payload_json: {
          start_date: trendDraft.value.tradeDate,
          start_price: trendDraft.value.price,
          end_date: payload.tradeDate,
          end_price: payload.price,
        },
      });
      trendDraft.value = null;
    }
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  }
}

async function handleRemoveAnnotation(annotationId: number): Promise<void> {
  try {
    await deleteChartAnnotation(annotationId);
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  }
}

async function handleClearAnnotations(): Promise<void> {
  if (!selectedSymbol.value) {
    return;
  }
  try {
    await clearChartAnnotations(selectedSymbol.value, "index");
    trendDraft.value = null;
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  }
}

watch(selectedIndicators, () => {
  if (selectedSymbol.value) {
    void loadChart();
  }
});

onMounted(async () => {
  selectedSymbol.value = String(route.query.symbol ?? "");
  await loadInstrumentOptions();
  if (selectedSymbol.value) {
    await loadChart();
  }
});
</script>

<style scoped>
.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.toolbar-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.85rem;
}

.quick-range,
.indicator-toggles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.toggle-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
}

.secondary-button {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 0.45rem 0.8rem;
  cursor: pointer;
}

.wide-field {
  min-width: 240px;
}

.highlights {
  margin: 0;
  padding-left: 1.1rem;
}
</style>
