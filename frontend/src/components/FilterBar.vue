<template>
  <section class="filter-bar panel">
    <div class="panel-body filter-bar-body">
      <div class="filter-bar-copy">
        <strong>{{ title }}</strong>
        <p v-if="description" class="muted">{{ description }}</p>
      </div>
      <div class="filter-bar-controls">
        <slot />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<style scoped>
.filter-bar-body {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.filter-bar-copy {
  display: grid;
  gap: 0.25rem;
}

.filter-bar-copy p,
.filter-bar-copy strong {
  margin: 0;
}

.filter-bar-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

@media (max-width: 960px) {
  .filter-bar-body {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
