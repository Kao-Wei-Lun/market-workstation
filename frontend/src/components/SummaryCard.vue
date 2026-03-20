<template>
  <article class="summary-card panel">
    <div class="panel-body">
      <span class="muted">{{ card.label }}</span>
      <strong>{{ card.display_value }}</strong>
      <span class="pill" :class="card.tone">{{ card.tone }}</span>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { DashboardSummaryCard } from "@/types/dashboard";

defineProps<{
  card: DashboardSummaryCard;
}>();
</script>

<style scoped>
.summary-card .panel-body {
  display: grid;
  gap: 0.45rem;
}

.summary-card strong {
  font-size: 1.45rem;
}
</style>
