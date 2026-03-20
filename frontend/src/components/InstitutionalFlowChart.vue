<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description" />
    </div>
    <div class="panel-body">
      <svg v-if="flowPoints.length" class="flow-svg" viewBox="0 0 960 260" role="img" aria-label="法人流向圖">
        <line x1="52" x2="920" y1="130" y2="130" class="baseline" />
        <g v-for="bar in plottedBars" :key="bar.tradeDate">
          <rect :x="bar.x - 9" :y="bar.futuresY" width="8" :height="bar.futuresHeight" class="futures-bar" rx="2" />
          <rect :x="bar.x + 1" :y="bar.optionsY" width="8" :height="bar.optionsHeight" class="options-bar" rx="2" />
        </g>
        <path :d="biasPath" class="bias-line" />
        <text
          v-for="tick in xTicks"
          :key="tick.label"
          :x="tick.x"
          y="246"
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
}>();

const left = 52;
const right = 920;
const baseline = 130;

const maxMagnitude = computed(() =>
  Math.max(
    ...props.flowPoints.map((point) =>
      Math.max(Math.abs(point.futures_net_open_interest), Math.abs(point.options_net_open_interest)),
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
  return baseline - (value / maxMagnitude.value) * 82;
}

const plottedBars = computed(() =>
  props.flowPoints.map((point, index) => {
    const futuresYEnd = yForValue(point.futures_net_open_interest);
    const optionsYEnd = yForValue(point.options_net_open_interest);
    return {
      tradeDate: point.trade_date,
      x: xForIndex(index),
      futuresY: Math.min(baseline, futuresYEnd),
      futuresHeight: Math.max(Math.abs(futuresYEnd - baseline), 2),
      optionsY: Math.min(baseline, optionsYEnd),
      optionsHeight: Math.max(Math.abs(optionsYEnd - baseline), 2),
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
      return `${command} ${xForIndex(index)} ${baseline - bias * 24}`;
    })
    .filter((item): item is string => Boolean(item));
  return segments.join(" ");
});

const xTicks = computed(() => {
  if (!props.flowPoints.length) {
    return [];
  }
  const indices = Array.from(new Set([0, Math.floor(props.flowPoints.length / 2), props.flowPoints.length - 1]));
  return indices.map((index) => ({ x: xForIndex(index), label: formatDate(props.flowPoints[index].trade_date) }));
});
</script>

<style scoped>
.flow-svg {
  width: 100%;
  min-width: 780px;
  height: auto;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(16, 38, 63, 0.04), rgba(255, 255, 255, 0.8));
}

.baseline {
  stroke: rgba(27, 46, 64, 0.14);
  stroke-width: 1;
}

.futures-bar {
  fill: rgba(22, 89, 146, 0.75);
}

.options-bar {
  fill: rgba(207, 124, 0, 0.75);
}

.bias-line {
  fill: none;
  stroke: #7b5ce1;
  stroke-width: 2;
}

.axis-label {
  font-size: 12px;
  fill: rgba(27, 46, 64, 0.7);
  text-anchor: middle;
}
</style>
