<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description">
        <div v-if="toolLabel || latestLabel" class="chart-header-meta">
          <span v-if="latestLabel" class="pill info">{{ latestLabel }}</span>
          <span v-if="toolLabel" class="pill">{{ toolLabel }}</span>
        </div>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <div v-if="candles.length" class="chart-shell">
        <svg
          ref="svgRef"
          class="chart-svg"
          viewBox="0 0 960 420"
          role="img"
          aria-label="K 線圖"
          @click="handlePlotClick"
        >
          <g>
            <line v-for="gridLine in gridLines" :key="`grid-${gridLine}`" :x1="52" :x2="920" :y1="gridLine" :y2="gridLine" class="grid-line" />
            <line x1="52" x2="920" :y1="volumeTop" :y2="volumeTop" class="grid-line heavy" />
          </g>

          <g v-for="candle in plottedCandles" :key="candle.tradeDate">
            <line
              :x1="candle.x"
              :x2="candle.x"
              :y1="candle.highY"
              :y2="candle.lowY"
              :class="['wick', candle.tone]"
            />
            <rect
              :x="candle.x - candleWidth / 2"
              :y="Math.min(candle.openY, candle.closeY)"
              :width="candleWidth"
              :height="Math.max(Math.abs(candle.closeY - candle.openY), 2)"
              :class="['candle', candle.tone]"
              rx="2"
            />
            <rect
              :x="candle.x - candleWidth / 2"
              :y="volumeBottom - candle.volumeHeight"
              :width="candleWidth"
              :height="candle.volumeHeight"
              :class="['volume-bar', candle.tone]"
              rx="1"
            />
          </g>

          <path
            v-for="line in overlayPaths"
            :key="line.key"
            :d="line.path"
            :stroke="line.color"
            class="overlay-line"
          />

          <g v-for="annotation in renderedAnnotations" :key="annotation.key">
            <line
              v-if="annotation.kind === 'horizontal'"
              x1="52"
              x2="920"
              :y1="annotation.y1"
              :y2="annotation.y1"
              class="annotation-line"
            />
            <line
              v-else
              :x1="annotation.x1"
              :x2="annotation.x2"
              :y1="annotation.y1"
              :y2="annotation.y2"
              class="annotation-line"
            />
          </g>

          <g v-if="draftLine">
            <line
              :x1="draftLine.x1"
              :x2="draftLine.x2"
              :y1="draftLine.y1"
              :y2="draftLine.y2"
              class="annotation-line draft"
            />
          </g>

          <g>
            <text
              v-for="tick in yAxisTicks"
              :key="`y-${tick.label}`"
              x="8"
              :y="tick.y + 4"
              class="axis-label"
            >
              {{ tick.label }}
            </text>
            <text
              v-for="tick in xAxisTicks"
              :key="`x-${tick.label}`"
              :x="tick.x"
              y="408"
              class="axis-label axis-label-x"
            >
              {{ tick.label }}
            </text>
          </g>
        </svg>
      </div>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import SectionHeader from "@/components/SectionHeader.vue";
import type { ChartAnnotationRead, ChartCandleRead } from "@/types/charts";
import type { ChartPlotClickPayload } from "@/utils/charts";
import { buildOverlayLines, latestCandle, parseNumeric } from "@/utils/charts";
import { formatDate, formatNumber } from "@/utils/formatters";

interface DraftPoint {
  tradeDate: string;
  price: number;
}

type RenderedAnnotation =
  | { key: string; kind: "horizontal"; y1: number }
  | { key: string; kind: "trend"; x1: number; x2: number; y1: number; y2: number };

const props = defineProps<{
  title: string;
  candles: ChartCandleRead[];
  indicators?: import("@/types/charts").ChartIndicatorSeriesRead[];
  annotations?: ChartAnnotationRead[];
  description?: string;
  activeTool?: string;
  draftTrendStart?: DraftPoint | null;
  emptyMessage?: string;
}>();

const emit = defineEmits<{
  (event: "plot-click", payload: ChartPlotClickPayload): void;
}>();

const svgRef = ref<SVGSVGElement | null>(null);
const top = 24;
const left = 52;
const right = 920;
const priceBottom = 270;
const volumeTop = 300;
const volumeBottom = 380;

const numericCandles = computed(() =>
  props.candles.map((candle) => ({
    tradeDate: candle.trade_date,
    open: parseNumeric(candle.open) ?? 0,
    high: parseNumeric(candle.high) ?? 0,
    low: parseNumeric(candle.low) ?? 0,
    close: parseNumeric(candle.close) ?? 0,
    volume: candle.volume,
  })),
);

const priceRange = computed(() => {
  const highs = numericCandles.value.map((candle) => candle.high);
  const lows = numericCandles.value.map((candle) => candle.low);
  const maxPrice = Math.max(...highs, 0);
  const minPrice = Math.min(...lows, maxPrice || 0);
  const padding = (maxPrice - minPrice || 1) * 0.08;
  return {
    min: minPrice - padding,
    max: maxPrice + padding,
  };
});

const maxVolume = computed(() => Math.max(...numericCandles.value.map((candle) => candle.volume), 0));
const candleWidth = computed(() => Math.max(6, Math.floor((right - left) / Math.max(props.candles.length * 1.6, 1))));

function xForIndex(index: number): number {
  if (props.candles.length <= 1) {
    return (left + right) / 2;
  }
  return left + ((right - left) * index) / (props.candles.length - 1);
}

function yForPrice(price: number): number {
  const range = priceRange.value.max - priceRange.value.min || 1;
  return top + ((priceRange.value.max - price) / range) * (priceBottom - top);
}

function yForVolume(volume: number): number {
  if (maxVolume.value <= 0) {
    return 0;
  }
  return ((volumeBottom - volumeTop) * volume) / maxVolume.value;
}

const plottedCandles = computed(() =>
  numericCandles.value.map((candle, index) => ({
    ...candle,
    x: xForIndex(index),
    openY: yForPrice(candle.open),
    highY: yForPrice(candle.high),
    lowY: yForPrice(candle.low),
    closeY: yForPrice(candle.close),
    volumeHeight: yForVolume(candle.volume),
    tone: candle.close >= candle.open ? "positive" : "negative",
  })),
);

const gridLines = computed(() => [top, top + 62, top + 124, top + 186, priceBottom]);

const yAxisTicks = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const price = priceRange.value.max - (priceRange.value.max - priceRange.value.min) * ratio;
    return { y: top + (priceBottom - top) * ratio, label: formatNumber(price.toFixed(2)) };
  }),
);

const xAxisTicks = computed(() => {
  if (!props.candles.length) {
    return [];
  }
  const indices = Array.from(new Set([0, Math.floor(props.candles.length / 2), props.candles.length - 1]));
  return indices.map((index) => ({
    x: xForIndex(index),
    label: formatDate(props.candles[index].trade_date),
  }));
});

const overlayPaths = computed(() =>
  buildOverlayLines(props.indicators ?? [])
    .map((line) => ({
      key: line.key,
      color: line.color,
      path: line.points
        .map((point, index) => {
          const candleIndex = props.candles.findIndex((candle) => candle.trade_date === point.tradeDate);
          if (candleIndex < 0) {
            return null;
          }
          const command = index === 0 ? "M" : "L";
          return `${command} ${xForIndex(candleIndex)} ${yForPrice(point.value)}`;
        })
        .filter((segment): segment is string => Boolean(segment))
        .join(" "),
    }))
    .filter((line) => line.path),
);

function findIndexByTradeDate(tradeDate: string): number {
  const index = props.candles.findIndex((candle) => candle.trade_date === tradeDate);
  return index >= 0 ? index : 0;
}

const renderedAnnotations = computed<RenderedAnnotation[]>(() =>
  (props.annotations ?? []).flatMap<RenderedAnnotation>((annotation) => {
    if (annotation.annotation_type === "horizontal_line") {
      const price = parseNumeric(annotation.payload_json.price as string | number | null | undefined);
      if (price === null) {
        return [];
      }
      return [{ key: `annotation-${annotation.id}`, kind: "horizontal" as const, y1: yForPrice(price) }];
    }
    const startDate = String(annotation.payload_json.start_date ?? "");
    const endDate = String(annotation.payload_json.end_date ?? "");
    const startPrice = parseNumeric(annotation.payload_json.start_price as string | number | null | undefined);
    const endPrice = parseNumeric(annotation.payload_json.end_price as string | number | null | undefined);
    if (!startDate || !endDate || startPrice === null || endPrice === null) {
      return [];
    }
    return [
      {
        key: `annotation-${annotation.id}`,
        kind: "trend" as const,
        x1: xForIndex(findIndexByTradeDate(startDate)),
        x2: xForIndex(findIndexByTradeDate(endDate)),
        y1: yForPrice(startPrice),
        y2: yForPrice(endPrice),
      },
    ];
  }),
);

const draftLine = computed(() => {
  if (!props.draftTrendStart || !numericCandles.value.length) {
    return null;
  }
  const latestIndex = numericCandles.value.length - 1;
  return {
    x1: xForIndex(findIndexByTradeDate(props.draftTrendStart.tradeDate)),
    y1: yForPrice(props.draftTrendStart.price),
    x2: xForIndex(latestIndex),
    y2: yForPrice(numericCandles.value[latestIndex].close),
  };
});

const latestLabel = computed(() => {
  const candle = latestCandle(props.candles);
  return candle ? `最新資料 ${formatDate(candle.trade_date)}` : "";
});

const toolLabel = computed(() => {
  if (!props.activeTool || props.activeTool === "none") {
    return "";
  }
  return props.activeTool === "horizontal_line" ? "目前工具：水平線" : "目前工具：趨勢線";
});

function handlePlotClick(event: MouseEvent): void {
  if (!svgRef.value || !props.candles.length) {
    return;
  }
  const rect = svgRef.value.getBoundingClientRect();
  const svgX = ((event.clientX - rect.left) / rect.width) * 960;
  const svgY = ((event.clientY - rect.top) / rect.height) * 420;
  if (svgX < left || svgX > right || svgY < top || svgY > priceBottom) {
    return;
  }
  const nearestIndex = Math.min(
    props.candles.length - 1,
    Math.max(0, Math.round(((svgX - left) / (right - left)) * Math.max(props.candles.length - 1, 1))),
  );
  const ratio = (svgY - top) / (priceBottom - top);
  const price = priceRange.value.max - (priceRange.value.max - priceRange.value.min) * ratio;
  emit("plot-click", {
    tradeDate: props.candles[nearestIndex].trade_date,
    price: Number(price.toFixed(2)),
  });
}
</script>

<style scoped>
.chart-shell {
  overflow-x: auto;
}

.chart-svg {
  width: 100%;
  min-width: 780px;
  height: auto;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(22, 89, 146, 0.04), rgba(255, 255, 255, 0.8));
}

.chart-header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.grid-line {
  stroke: rgba(27, 46, 64, 0.08);
  stroke-width: 1;
}

.grid-line.heavy {
  stroke: rgba(27, 46, 64, 0.12);
  stroke-dasharray: 3 3;
}

.wick,
.annotation-line,
.overlay-line {
  fill: none;
}

.wick.positive,
.candle.positive,
.volume-bar.positive {
  stroke: #1b7f5a;
  fill: rgba(27, 127, 90, 0.75);
}

.wick.negative,
.candle.negative,
.volume-bar.negative {
  stroke: #b54335;
  fill: rgba(181, 67, 53, 0.75);
}

.overlay-line {
  stroke-width: 2;
}

.annotation-line {
  stroke: #165992;
  stroke-width: 2;
  stroke-dasharray: 6 4;
}

.annotation-line.draft {
  opacity: 0.5;
}

.axis-label {
  font-size: 12px;
  fill: rgba(27, 46, 64, 0.7);
}

.axis-label-x {
  text-anchor: middle;
}
</style>
