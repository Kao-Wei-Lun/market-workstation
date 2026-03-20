<template>
  <div class="drawing-toolbar">
    <span class="toolbar-label">畫線工具</span>
    <div class="tool-buttons">
      <button
        v-for="tool in tools"
        :key="tool.value"
        type="button"
        :class="['tool-button', { active: modelValue === tool.value }]"
        @click="$emit('update:modelValue', tool.value)"
      >
        {{ tool.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChartDrawingTool } from "@/utils/charts";

defineProps<{
  modelValue: ChartDrawingTool;
}>();

defineEmits<{
  (event: "update:modelValue", value: ChartDrawingTool): void;
}>();

const tools: Array<{ value: ChartDrawingTool; label: string }> = [
  { value: "none", label: "不啟用" },
  { value: "trend_line", label: "趨勢線" },
  { value: "horizontal_line", label: "水平線" },
  { value: "vertical_line", label: "垂直線" },
  { value: "range_box", label: "區間框" },
  { value: "point_marker", label: "重點標記" },
];
</script>

<style scoped>
.drawing-toolbar {
  display: grid;
  gap: 0.5rem;
}

.toolbar-label {
  font-size: 0.86rem;
  color: var(--text-muted);
}

.tool-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.tool-button {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 0.5rem 0.85rem;
  cursor: pointer;
  color: var(--text);
}

.tool-button.active {
  border-color: rgba(22, 89, 146, 0.35);
  background: rgba(22, 89, 146, 0.12);
  color: #165992;
}
</style>
