<template>
  <section class="metric-grid">
    <article v-for="metric in metrics" :key="metric.label" class="metric-card panel">
      <div class="panel-body">
        <span class="muted">{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <span v-if="metric.hint" class="metric-hint">{{ metric.hint }}</span>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  metrics: { label: string; value: string; hint?: string }[];
}>();
</script>

<style scoped>
.metric-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.metric-card .panel-body {
  display: grid;
  gap: 0.35rem;
}

.metric-card strong {
  font-size: 1.25rem;
}

.metric-hint {
  color: var(--muted);
  font-size: 0.82rem;
}
</style>
