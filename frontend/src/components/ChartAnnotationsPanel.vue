<template>
  <DetailPanel title="畫線與注記" :description="description">
    <div v-if="annotations.length" class="annotation-list">
      <div v-for="annotation in annotations" :key="annotation.id" class="annotation-item">
        <div>
          <strong>{{ describeAnnotation(annotation) }}</strong>
          <p class="muted">{{ formatDateTime(annotation.created_at) }}</p>
        </div>
        <button type="button" class="secondary-button" @click="$emit('remove', annotation.id)">移除</button>
      </div>
    </div>
    <EmptyState
      v-else
      title="尚無畫線"
      message="選擇趨勢線或水平線工具後，直接點擊 K 線圖即可新增注記。"
    />
    <button
      v-if="annotations.length"
      type="button"
      class="secondary-button clear-button"
      @click="$emit('clear')"
    >
      清除全部畫線
    </button>
  </DetailPanel>
</template>

<script setup lang="ts">
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import type { ChartAnnotationRead } from "@/types/charts";
import { describeAnnotation } from "@/utils/charts";
import { formatDateTime } from "@/utils/formatters";

defineProps<{
  annotations: ChartAnnotationRead[];
  description?: string;
}>();

defineEmits<{
  (event: "remove", annotationId: number): void;
  (event: "clear"): void;
}>();
</script>

<style scoped>
.annotation-list {
  display: grid;
  gap: 0.75rem;
}

.annotation-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel-alt);
}

.annotation-item p {
  margin: 0.2rem 0 0;
}

.secondary-button {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 0.5rem 0.85rem;
  cursor: pointer;
}

.clear-button {
  margin-top: 0.9rem;
}
</style>
