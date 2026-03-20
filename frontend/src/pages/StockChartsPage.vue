<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="圖表"
      title="個股 K 線圖"
      description="查看個股／ETF 日線、成交量、指標覆蓋與基本畫線。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'reports', query: { search: selectedSymbol || undefined } }">
          查看相關報表
        </RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'candidates', query: { search: selectedSymbol || undefined } }">
          查看候選
        </RouterLink>
      </div>
    </PageHeader>

    <FilterBar title="圖表篩選" description="切換市場、標的、日期區間、指標與畫線工具。">
      <div class="form-inline">
        <div class="field-group">
          <label for="stock-chart-market">市場</label>
          <select id="stock-chart-market" v-model="selectedMarket" @change="loadInstrumentOptions">
            <option value="TW">台灣</option>
            <option value="US">美國</option>
          </select>
        </div>
        <div class="field-group">
          <label for="stock-chart-query">搜尋</label>
          <input id="stock-chart-query" v-model="instrumentQuery" placeholder="代號或名稱" @input="loadInstrumentOptions" />
        </div>
        <div class="field-group wide-field">
          <label for="stock-chart-symbol">標的</label>
          <select id="stock-chart-symbol" v-model="selectedSymbol" @change="loadChart">
            <option v-for="instrument in instruments" :key="instrument.symbol" :value="instrument.symbol">
              {{ instrument.symbol }} / {{ instrument.name }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="stock-date-from">起始</label>
          <input id="stock-date-from" v-model="dateFrom" type="date" />
        </div>
        <div class="field-group">
          <label for="stock-date-to">結束</label>
          <input id="stock-date-to" v-model="dateTo" type="date" />
        </div>
        <div class="field-group">
          <label for="stock-tool">畫線工具</label>
          <select id="stock-tool" v-model="activeTool">
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
      title="圖表資料狀態"
      :as-of-date="chartData?.instrument.latest_data_date ?? null"
      :generated-at="null"
      :item-count="chartData?.candles.length"
      hint="圖表頁目前使用日線 OHLCV、已保存指標與本機畫線注記。"
      demo-hint="若圖表沒有內容，請先執行 make demo-data 或載入對應 universe。"
      :show-refresh="true"
      @refresh="loadChart"
    />

    <LoadingState v-if="isLoading" message="正在載入個股圖表..." />
    <ErrorState
      v-else-if="errorMessage"
      title="圖表載入失敗"
      message="無法載入 K 線圖資料。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="!chartData || !chartData.candles.length"
      title="尚無圖表資料"
      message="目前選定標的尚未有可顯示的日線資料。"
    />
    <template v-else>
      <div class="page-section-grid">
        <DetailPanel title="圖表摘要" description="顯示目前標的的基本資訊、最新收盤與指標覆蓋。">
          <MetricGrid :metrics="overviewMetrics" />
        </DetailPanel>
        <ChartAnnotationsPanel
          :annotations="chartData.annotations"
          description="畫線會保存在本機資料庫，之後再開同一標的時仍可沿用。"
          @remove="handleRemoveAnnotation"
          @clear="handleClearAnnotations"
        />
      </div>

      <CandlestickChart
        title="日線 K 線圖"
        description="上半部為 K 線與指標覆蓋，下半部為成交量。"
        :candles="chartData.candles"
        :indicators="visibleIndicators"
        :annotations="chartData.annotations"
        :active-tool="activeTool"
        :draft-trend-start="trendDraft"
        empty-message="目前沒有可用日線資料。"
        @plot-click="handlePlotClick"
      />

      <DetailPanel title="操作提示" description="第一版畫線支援趨勢線、水平線與清除。">
        <ul class="highlights">
          <li>選擇「水平線」後點擊圖表，即會在對應價位建立水平線。</li>
          <li>選擇「趨勢線」後連點兩次圖表，會以兩個日期／價位建立趨勢線。</li>
          <li>畫線目前以單一標的＋視圖類型保存，供本機研究持續使用。</li>
        </ul>
      </DetailPanel>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { clearChartAnnotations, createChartAnnotation, deleteChartAnnotation, fetchChartData, fetchChartInstruments } from "@/api/charts";
import { normalizeApiError } from "@/api/http";
import CandlestickChart from "@/components/CandlestickChart.vue";
import ChartAnnotationsPanel from "@/components/ChartAnnotationsPanel.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import PageHeader from "@/components/PageHeader.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import type { ChartDataRead, ChartIndicatorSeriesRead, ChartInstrumentRead } from "@/types/charts";
import type { ChartPlotClickPayload } from "@/utils/charts";
import { buildDateRange, latestCandle } from "@/utils/charts";
import { formatDate, formatNumber, formatPercent } from "@/utils/formatters";

const route = useRoute();
const router = useRouter();
const instruments = ref<ChartInstrumentRead[]>([]);
const chartData = ref<ChartDataRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedMarket = ref("TW");
const instrumentQuery = ref("");
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

const overviewMetrics = computed(() => {
  if (!chartData.value) {
    return [];
  }
  const latest = latestCandle(chartData.value.candles);
  return [
    { label: "標的", value: `${chartData.value.instrument.symbol} / ${chartData.value.instrument.name}`, hint: chartData.value.instrument.market },
    { label: "最新日期", value: formatDate(chartData.value.instrument.latest_data_date), hint: "資料日期" },
    { label: "最新收盤", value: formatNumber(latest?.close ?? null), hint: "close" },
    { label: "漲跌幅", value: formatPercent(latest?.change_percent ?? null), hint: "change %" },
    { label: "指標數量", value: formatNumber(chartData.value.indicators.length), hint: "已保存 overlays" },
    { label: "畫線數量", value: formatNumber(chartData.value.annotations.length), hint: "本機持久化注記" },
  ];
});

async function loadInstrumentOptions(): Promise<void> {
  try {
    const response = await fetchChartInstruments({
      market: selectedMarket.value,
      query: instrumentQuery.value || undefined,
      limit: 50,
    });
    instruments.value = response.filter((instrument) => instrument.asset_type !== "index");
    if (!selectedSymbol.value && instruments.value.length) {
      selectedSymbol.value = String(route.query.symbol ?? instruments.value[0].symbol);
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
    chartData.value = await fetchChartData(selectedSymbol.value, {
      dateFrom: dateFrom.value || undefined,
      dateTo: dateTo.value || undefined,
      indicatorNames: selectedIndicators.value,
      viewKind: "instrument",
    });
    await router.replace({
      name: "stock-charts",
      query: {
        symbol: selectedSymbol.value,
        market: selectedMarket.value,
      },
    });
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
        view_kind: "instrument",
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
        view_kind: "instrument",
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
    await clearChartAnnotations(selectedSymbol.value, "instrument");
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
  selectedMarket.value = String(route.query.market ?? "TW");
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
