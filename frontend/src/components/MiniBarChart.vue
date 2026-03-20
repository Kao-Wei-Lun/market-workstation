<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description" />
    </div>
    <div class="panel-body">
      <div v-if="normalizedPoints.length" class="chart-stack">
        <div v-for="point in normalizedPoints" :key="point.label" class="chart-row">
          <div class="chart-label-row">
            <span>{{ point.label }}</span>
            <strong>{{ formatValue(point.value) }}</strong>
          </div>
          <div class="chart-track">
            <div class="chart-fill" :class="point.tone ?? 'info'" :style="{ width: `${point.percentage}%` }" />
          </div>
        </div>
      </div>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import SectionHeader from "@/components/SectionHeader.vue";
import type { ChartPointInput } from "@/utils/presentation";
import { buildChartPoints } from "@/utils/presentation";

const props = defineProps<{
  title: string;
  points: ChartPointInput[];
  description?: string;
  emptyMessage?: string;
}>();

const normalizedPoints = computed(() => buildChartPoints(props.points));

function formatValue(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}
</script>

<style scoped>
.chart-stack {
  display: grid;
  gap: 0.85rem;
}

.chart-row {
  display: grid;
  gap: 0.35rem;
}

.chart-label-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
}

.chart-track {
  height: 10px;
  border-radius: 999px;
  background: var(--panel-alt);
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  border-radius: 999px;
}

.chart-fill.positive {
  background: var(--positive);
}

.chart-fill.negative {
  background: var(--negative);
}

.chart-fill.neutral {
  background: var(--neutral);
}

.chart-fill.info {
  background: var(--accent);
}
</style>
