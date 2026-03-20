<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="圖表"
      title="市場結構圖"
      description="以大盤日線對照外資現貨、期貨、選擇權方向與 bias，作為盤後研究入口。"
    >
      <div class="page-actions">
        <RouterLink class="pill link-pill" :to="{ name: 'derivatives' }">查看衍生性商品摘要</RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
          查看當日報表
        </RouterLink>
        <RouterLink class="pill link-pill" :to="{ name: 'candidates', query: { candidateDate: selectedTradeDate || undefined } }">
          查看候選
        </RouterLink>
      </div>
    </PageHeader>

    <FilterBar title="市場結構篩選" description="切換指數、日期區間、顯示序列與畫線工具。">
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
        <div class="series-toggles">
          <label class="toggle-pill"><input v-model="showSpot" type="checkbox" /> 現貨買賣超</label>
          <label class="toggle-pill"><input v-model="showFutures" type="checkbox" /> 期貨淨部位</label>
          <label class="toggle-pill"><input v-model="showOptions" type="checkbox" /> 選擇權方向</label>
          <label class="toggle-pill"><input v-model="showBias" type="checkbox" /> Bias 線</label>
        </div>
      </div>
      <ChartDrawingToolbar v-model="activeTool" />
    </FilterBar>

    <PageStatusBar
      title="市場結構資料狀態"
      :as-of-date="marketStructure?.summary.trade_date ?? chartData?.instrument.latest_data_date ?? null"
      :generated-at="null"
      :item-count="chartData?.candles.length"
      hint="同一頁整合大盤日線、外資現貨、期貨、選擇權方向與 bias interpretation。"
      demo-hint="若內容為空，請先執行 make demo-data 或補載相關日資料。"
      :show-refresh="true"
      @refresh="loadChart"
    />

    <LoadingState v-if="isLoading" message="正在載入市場結構圖..." />
    <ErrorState
      v-else-if="errorMessage"
      title="市場結構圖載入失敗"
      message="無法載入大盤、外資流向或市場結構摘要。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="!chartData || !chartData.candles.length"
      title="尚無市場結構資料"
      message="目前選定指數尚未有可顯示的大盤日線與結構資料。"
    />
    <template v-else-if="chartData && marketStructure">
      <div class="page-section-grid">
        <DetailPanel title="市場結構摘要" description="快速檢查目前 regime、方向與分歧訊號。">
          <MetricGrid :metrics="marketMetrics" />
        </DetailPanel>
        <DetailPanel title="解讀提示" description="將外資現貨、期貨、選擇權與大盤方向整理成可直接閱讀的提示。">
          <template #header>
            <div class="detail-actions">
              <RouterLink class="detail-link" :to="{ name: 'reports', query: { reportDate: selectedTradeDate || undefined } }">
                查看同日報表
              </RouterLink>
              <RouterLink class="detail-link" :to="{ name: 'derivatives' }">查看衍生性商品頁</RouterLink>
            </div>
          </template>
          <ul class="highlights">
            <li v-for="item in interpretationHighlights" :key="item">{{ item }}</li>
          </ul>
        </DetailPanel>
        <ChartAnnotationsPanel
          :annotations="chartData.annotations"
          description="市場結構頁的畫線可保留對大盤的重要區間與關鍵轉折。"
          :feedback-message="annotationFeedback"
          :feedback-tone="annotationFeedbackTone"
          @remove="handleRemoveAnnotation"
          @clear="handleClearAnnotations"
        />
      </div>

      <CandlestickChart
        title="大盤日線 K 線圖"
        description="顯示指數日線、成交量與已保存的技術指標 overlay。"
        :candles="chartData.candles"
        :indicators="visibleIndicators"
        :annotations="chartData.annotations"
        :active-tool="activeTool"
        :draft-trend-start="trendDraft"
        empty-message="目前沒有大盤日線資料。"
        @plot-click="handlePlotClick"
      />

      <MarketStructureFlowChart
        title="外資市場結構流向"
        description="同步顯示現貨買賣超、期貨淨部位、選擇權方向與 bias 線。點擊日期可切換下方明細。"
        :flow-points="marketStructure.flow_points"
        :show-spot="showSpot"
        :show-futures="showFutures"
        :show-options="showOptions"
        :show-bias="showBias"
        :selected-trade-date="selectedTradeDate"
        empty-message="目前沒有可用的市場結構序列。"
        @select-trade-date="handleSelectTradeDate"
      />

      <div class="page-section-grid">
        <DetailPanel title="選定日期明細" description="以選定日期作為簡易 tooltip / 檢視面板，方便日常複盤。">
          <MetricGrid :metrics="selectedDateMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="流向強弱"
          description="比較選定日期的現貨、期貨與選擇權方向強度。"
          :points="selectedDateChartPoints"
          empty-message="請先選擇一個日期。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import {
  clearChartAnnotations,
  createChartAnnotation,
  deleteChartAnnotation,
  fetchChartData,
  fetchChartInstruments,
  fetchMarketStructureChart,
} from "@/api/charts";
import { normalizeApiError } from "@/api/http";
import CandlestickChart from "@/components/CandlestickChart.vue";
import ChartAnnotationsPanel from "@/components/ChartAnnotationsPanel.vue";
import ChartDrawingToolbar from "@/components/ChartDrawingToolbar.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MarketStructureFlowChart from "@/components/MarketStructureFlowChart.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageHeader from "@/components/PageHeader.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import type {
  ChartDataRead,
  ChartIndicatorSeriesRead,
  ChartInstrumentRead,
  InstitutionalFlowPointRead,
  MarketStructureChartRead,
} from "@/types/charts";
import type { ChartDrawingTool, ChartPlotClickPayload } from "@/utils/charts";
import { buildDateRange, chartToolLabel, latestCandle, parseNumeric } from "@/utils/charts";
import { formatDate, formatNumber, formatPercent } from "@/utils/formatters";

const route = useRoute();
const router = useRouter();
const instruments = ref<ChartInstrumentRead[]>([]);
const chartData = ref<ChartDataRead | null>(null);
const marketStructure = ref<MarketStructureChartRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedSymbol = ref("");
const dateFrom = ref("");
const dateTo = ref("");
const selectedIndicators = ref<string[]>(["sma", "ema"]);
const activeTool = ref<ChartDrawingTool>("none");
const trendDraft = ref<ChartPlotClickPayload | null>(null);
const annotationFeedback = ref<string | null>(null);
const annotationFeedbackTone = ref<"info" | "success" | "error">("info");
const showSpot = ref(true);
const showFutures = ref(true);
const showOptions = ref(true);
const showBias = ref(true);
const selectedTradeDate = ref("");

const availableIndicators = ["sma", "ema", "bollinger", "supertrend"];

const visibleIndicators = computed<ChartIndicatorSeriesRead[]>(() =>
  (chartData.value?.indicators ?? []).filter((series) => selectedIndicators.value.includes(series.indicator_name)),
);

const selectedFlowPoint = computed<InstitutionalFlowPointRead | null>(() => {
  const points = marketStructure.value?.flow_points ?? [];
  if (!points.length) {
    return null;
  }
  return points.find((point) => point.trade_date === selectedTradeDate.value) ?? points[points.length - 1];
});

const interpretationHighlights = computed(() => {
  if (!marketStructure.value) {
    return [];
  }
  return [
    ...marketStructure.value.summary.highlights,
    ...marketStructure.value.summary.divergence_hints,
    ...marketStructure.value.summary.anomaly_hints,
  ];
});

const marketMetrics = computed(() => {
  if (!chartData.value || !marketStructure.value) {
    return [];
  }
  const latest = latestCandle(chartData.value.candles);
  return [
    { label: "指數", value: `${chartData.value.instrument.symbol} / ${chartData.value.instrument.name}`, hint: "大盤標的" },
    { label: "最新日期", value: formatDate(marketStructure.value.summary.trade_date), hint: "市場結構日期" },
    { label: "收盤", value: formatNumber(latest?.close ?? null), hint: "最新 close" },
    { label: "漲跌幅", value: formatPercent(latest?.change_percent ?? null), hint: "當日變化" },
    { label: "Regime", value: marketStructure.value.summary.overall_regime, hint: "法人偏向結論" },
    { label: "現貨方向", value: marketStructure.value.summary.spot_direction, hint: "外資現貨" },
    { label: "期貨方向", value: marketStructure.value.summary.futures_direction, hint: "外資期貨" },
    { label: "選擇權方向", value: marketStructure.value.summary.options_direction, hint: "外資選擇權" },
  ];
});

const selectedDateMetrics = computed(() => {
  if (!selectedFlowPoint.value) {
    return [];
  }
  return [
    { label: "交易日期", value: formatDate(selectedFlowPoint.value.trade_date), hint: "目前選定日期" },
    { label: "現貨買賣超", value: formatNumber(selectedFlowPoint.value.spot_net_amount), hint: "外資現貨淨額" },
    { label: "期貨淨部位", value: formatNumber(selectedFlowPoint.value.futures_net_open_interest), hint: "淨未平倉口數" },
    { label: "選擇權方向", value: formatNumber(selectedFlowPoint.value.options_directional_bias), hint: "方向性 bias" },
    { label: "整體 bias", value: formatNumber(selectedFlowPoint.value.average_bias_score), hint: "法人平均分數" },
    { label: "異常數", value: formatNumber(selectedFlowPoint.value.anomaly_count), hint: "異常提示" },
  ];
});

const selectedDateChartPoints = computed(() => {
  if (!selectedFlowPoint.value) {
    return [];
  }
  return [
    { label: "現貨", value: parseNumeric(selectedFlowPoint.value.spot_net_amount) ?? 0, tone: "positive" as const },
    { label: "期貨", value: selectedFlowPoint.value.futures_net_open_interest, tone: "info" as const },
    { label: "選擇權", value: (parseNumeric(selectedFlowPoint.value.options_directional_bias) ?? 0) * 100, tone: "negative" as const },
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
    const [chartResponse, structureResponse] = await Promise.all([
      fetchChartData(selectedSymbol.value, {
        dateFrom: dateFrom.value || undefined,
        dateTo: dateTo.value || undefined,
        indicatorNames: selectedIndicators.value,
        viewKind: "market_flow",
      }),
      fetchMarketStructureChart(selectedSymbol.value, {
        dateFrom: dateFrom.value || undefined,
        dateTo: dateTo.value || undefined,
      }),
    ]);
    chartData.value = chartResponse;
    marketStructure.value = structureResponse;
    selectedTradeDate.value = structureResponse.summary.trade_date ?? "";
    await router.replace({ name: "market-charts", query: { symbol: selectedSymbol.value, tradeDate: selectedTradeDate.value || undefined } });
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

function handleSelectTradeDate(tradeDate: string): void {
  selectedTradeDate.value = tradeDate;
}

async function handlePlotClick(payload: ChartPlotClickPayload): Promise<void> {
  if (!selectedSymbol.value || activeTool.value === "none") {
    return;
  }
  try {
    if (activeTool.value === "horizontal_line") {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "market_flow",
        annotation_type: "horizontal_line",
        label: `水平 ${payload.price}`,
        payload_json: { price: payload.price, trade_date: payload.tradeDate },
      });
      annotationFeedback.value = `已新增水平線：${payload.tradeDate} / ${payload.price}`;
      annotationFeedbackTone.value = "success";
    } else if (activeTool.value === "vertical_line") {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "market_flow",
        annotation_type: "vertical_line",
        label: `垂直 ${payload.tradeDate}`,
        payload_json: { trade_date: payload.tradeDate },
      });
      annotationFeedback.value = `已新增垂直線：${payload.tradeDate}`;
      annotationFeedbackTone.value = "success";
    } else if (activeTool.value === "point_marker") {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "market_flow",
        annotation_type: "point_marker",
        label: `標記 ${payload.tradeDate}`,
        payload_json: { trade_date: payload.tradeDate, price: payload.price },
      });
      annotationFeedback.value = `已新增重點標記：${payload.tradeDate} / ${payload.price}`;
      annotationFeedbackTone.value = "success";
    } else if (!trendDraft.value) {
      trendDraft.value = payload;
      annotationFeedback.value = `已記錄第一點，請再點一次完成${chartToolLabel(activeTool.value)}。`;
      annotationFeedbackTone.value = "info";
      return;
    } else {
      await createChartAnnotation({
        symbol: selectedSymbol.value,
        view_kind: "market_flow",
        annotation_type: activeTool.value,
        label: `${chartToolLabel(activeTool.value)} ${trendDraft.value.tradeDate}`,
        payload_json: {
          start_date: trendDraft.value.tradeDate,
          start_price: trendDraft.value.price,
          end_date: payload.tradeDate,
          end_price: payload.price,
        },
      });
      annotationFeedback.value = `已新增${chartToolLabel(activeTool.value)}。`;
      annotationFeedbackTone.value = "success";
      trendDraft.value = null;
    }
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
    annotationFeedback.value = "畫線儲存失敗，請稍後再試。";
    annotationFeedbackTone.value = "error";
  }
}

async function handleRemoveAnnotation(annotationId: number): Promise<void> {
  try {
    await deleteChartAnnotation(annotationId);
    annotationFeedback.value = "已移除畫線。";
    annotationFeedbackTone.value = "success";
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
    annotationFeedback.value = "移除畫線失敗。";
    annotationFeedbackTone.value = "error";
  }
}

async function handleClearAnnotations(): Promise<void> {
  if (!selectedSymbol.value) {
    return;
  }
  try {
    await clearChartAnnotations(selectedSymbol.value, "market_flow");
    trendDraft.value = null;
    annotationFeedback.value = "已清除目前市場結構圖的全部畫線。";
    annotationFeedbackTone.value = "success";
    await loadChart();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
    annotationFeedback.value = "清除畫線失敗。";
    annotationFeedbackTone.value = "error";
  }
}

watch(selectedIndicators, () => {
  if (selectedSymbol.value) {
    void loadChart();
  }
});

watch(activeTool, () => {
  trendDraft.value = null;
});

onMounted(async () => {
  selectedSymbol.value = String(route.query.symbol ?? "");
  selectedTradeDate.value = String(route.query.tradeDate ?? "");
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
.indicator-toggles,
.series-toggles {
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
