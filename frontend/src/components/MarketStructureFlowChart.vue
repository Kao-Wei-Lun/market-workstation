<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description">
        <div class="legend-list">
          <span v-if="showSpot" class="legend-item"><span class="legend-dot spot" /> 現貨</span>
          <span v-if="showFutures" class="legend-item"><span class="legend-dot futures" /> 期貨</span>
          <span v-if="showOptions" class="legend-item"><span class="legend-dot options" /> 選擇權</span>
          <span v-if="showBias" class="legend-item"><span class="legend-dot bias" /> Bias</span>
        </div>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <svg
        v-if="flowPoints.length"
        class="flow-svg"
        viewBox="0 0 960 300"
        role="img"
        aria-label="市場結構流向圖"
        @click="handleClick"
      >
        <line x1="52" x2="920" y1="150" y2="150" class="baseline" />
        <g v-for="bar in plottedBars" :key="bar.tradeDate">
          <rect
            v-if="showSpot"
            :x="bar.x - 15"
            :y="bar.spotY"
            width="8"
            :height="bar.spotHeight"
            class="spot-bar"
            :class="{ selected: selectedTradeDate === bar.tradeDate }"
            rx="2"
          />
          <rect
            v-if="showFutures"
            :x="bar.x - 4"
            :y="bar.futuresY"
            width="8"
            :height="bar.futuresHeight"
            class="futures-bar"
            :class="{ selected: selectedTradeDate === bar.tradeDate }"
            rx="2"
          />
          <rect
            v-if="showOptions"
            :x="bar.x + 7"
            :y="bar.optionsY"
            width="8"
            :height="bar.optionsHeight"
            class="options-bar"
            :class="{ selected: selectedTradeDate === bar.tradeDate }"
            rx="2"
          />
        </g>
        <path v-if="showBias" :d="biasPath" class="bias-line" />
        <text
          v-for="tick in xTicks"
          :key="tick.label"
          :x="tick.x"
          y="284"
          class="axis-label"
        >
          {{ tick.label }}
        </text>
      </svg>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import SectionHeader from "@/components/SectionHeader.vue";
import type { InstitutionalFlowPointRead } from "@/types/charts";
import { parseNumeric } from "@/utils/charts";
import { formatDate } from "@/utils/formatters";

const props = defineProps<{
  title: string;
  flowPoints: InstitutionalFlowPointRead[];
  description?: string;
  emptyMessage?: string;
  showSpot?: boolean;
  showFutures?: boolean;
  showOptions?: boolean;
  showBias?: boolean;
  selectedTradeDate?: string | null;
}>();

const emit = defineEmits<{
  (event: "select-trade-date", tradeDate: string): void;
}>();

const left = 52;
const right = 920;
const baseline = 150;

const maxMagnitude = computed(() =>
  Math.max(
    ...props.flowPoints.map((point) =>
      Math.max(
        Math.abs(parseNumeric(point.spot_net_amount) ?? 0),
        Math.abs(point.futures_net_open_interest),
        Math.abs(parseNumeric(point.options_directional_bias) ?? 0) * 100,
      ),
    ),
    1,
  ),
);

function xForIndex(index: number): number {
  if (props.flowPoints.length <= 1) {
    return (left + right) / 2;
  }
  return left + ((right - left) * index) / (props.flowPoints.length - 1);
}

function yForValue(value: number): number {
  return baseline - (value / maxMagnitude.value) * 102;
}

const plottedBars = computed(() =>
  props.flowPoints.map((point, index) => {
    const spotValue = parseNumeric(point.spot_net_amount) ?? 0;
    const optionsValue = (parseNumeric(point.options_directional_bias) ?? 0) * 100;
    const spotEnd = yForValue(spotValue);
    const futuresEnd = yForValue(point.futures_net_open_interest);
    const optionsEnd = yForValue(optionsValue);
    return {
      tradeDate: point.trade_date,
      x: xForIndex(index),
      spotY: Math.min(baseline, spotEnd),
      spotHeight: Math.max(Math.abs(spotEnd - baseline), 2),
      futuresY: Math.min(baseline, futuresEnd),
      futuresHeight: Math.max(Math.abs(futuresEnd - baseline), 2),
      optionsY: Math.min(baseline, optionsEnd),
      optionsHeight: Math.max(Math.abs(optionsEnd - baseline), 2),
    };
  }),
);

const biasPath = computed(() => {
  const segments = props.flowPoints
    .map((point, index) => {
      const bias = parseNumeric(point.average_bias_score);
      if (bias === null) {
        return null;
      }
      const command = index === 0 ? "M" : "L";
      return `${command} ${xForIndex(index)} ${baseline - bias * 30}`;
    })
    .filter((segment): segment is string => Boolean(segment));
  return segments.join(" ");
});

const xTicks = computed(() => {
  if (!props.flowPoints.length) {
    return [];
  }
  const indices = Array.from(new Set([0, Math.floor(props.flowPoints.length / 2), props.flowPoints.length - 1]));
  return indices.map((index) => ({
    x: xForIndex(index),
    label: formatDate(props.flowPoints[index].trade_date),
  }));
});

function handleClick(event: MouseEvent): void {
  if (!props.flowPoints.length) {
    return;
  }
  const target = event.currentTarget as SVGElement;
  const rect = target.getBoundingClientRect();
  const svgX = ((event.clientX - rect.left) / rect.width) * 960;
  const nearestIndex = Math.min(
    props.flowPoints.length - 1,
    Math.max(0, Math.round(((svgX - left) / (right - left)) * Math.max(props.flowPoints.length - 1, 1))),
  );
  emit("select-trade-date", props.flowPoints[nearestIndex].trade_date);
}
</script>

<style scoped>
.flow-svg {
  width: 100%;
  min-width: 780px;
  height: auto;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(16, 38, 63, 0.04), rgba(255, 255, 255, 0.8));
}

.legend-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.88rem;
  color: rgba(27, 46, 64, 0.76);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.legend-dot.spot,
.spot-bar {
  background: rgba(39, 111, 74, 0.75);
  fill: rgba(39, 111, 74, 0.75);
}

.legend-dot.futures,
.futures-bar {
  background: rgba(22, 89, 146, 0.78);
  fill: rgba(22, 89, 146, 0.78);
}

.legend-dot.options,
.options-bar {
  background: rgba(207, 124, 0, 0.78);
  fill: rgba(207, 124, 0, 0.78);
}

.legend-dot.bias {
  background: #7b5ce1;
}

.bias-line {
  fill: none;
  stroke: #7b5ce1;
  stroke-width: 2;
}

.baseline {
  stroke: rgba(27, 46, 64, 0.14);
  stroke-width: 1;
}

.spot-bar.selected,
.futures-bar.selected,
.options-bar.selected {
  stroke: rgba(27, 46, 64, 0.85);
  stroke-width: 2;
}

.axis-label {
  font-size: 12px;
  fill: rgba(27, 46, 64, 0.7);
  text-anchor: middle;
}
</style>
