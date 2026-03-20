<template>
  <div class="state-box panel">
    <div class="panel-body">
      <strong>Loading...</strong>
      <p class="muted">{{ message }}</p>
      <div class="skeleton-stack" aria-hidden="true">
        <span class="skeleton-line short" />
        <span class="skeleton-line" />
        <span class="skeleton-line medium" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ message?: string }>();
</script>

<style scoped>
.state-box {
  min-height: 140px;
  display: grid;
  place-items: center;
  text-align: center;
}

.skeleton-stack {
  width: min(280px, 100%);
  display: grid;
  gap: 0.45rem;
  margin-top: 0.9rem;
}

.skeleton-line {
  display: block;
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--panel-alt) 0%, #dfeaf6 50%, var(--panel-alt) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.skeleton-line.short {
  width: 52%;
}

.skeleton-line.medium {
  width: 74%;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}
</style>
