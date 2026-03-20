<template>
  <span class="pill score-badge" :class="tone">
    {{ label }} {{ displayValue }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { formatNumber } from "@/utils/formatters";

const props = defineProps<{
  label: string;
  value: string | number | null | undefined;
}>();

const numericValue = computed(() => Number(props.value ?? 0));
const tone = computed(() => {
  if (Number.isNaN(numericValue.value)) {
    return "neutral";
  }
  if (numericValue.value > 0) {
    return "positive";
  }
  if (numericValue.value < 0) {
    return "negative";
  }
  return "neutral";
});
const displayValue = computed(() => formatNumber(props.value));
</script>

<style scoped>
.score-badge {
  font-weight: 600;
}
</style>
