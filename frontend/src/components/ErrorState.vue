<template>
  <div class="state-box panel error-state">
    <div class="panel-body">
      <strong>{{ title }}</strong>
      <p class="muted">{{ message }}</p>
      <p v-if="detail" class="detail">{{ detail }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string;
  message: string;
  detail?: string | null;
}>();
</script>

<style scoped>
.state-box {
  min-height: 140px;
  display: grid;
  place-items: center;
  text-align: center;
}

.error-state {
  border-color: rgba(175, 63, 70, 0.18);
}

.detail {
  margin: 0;
  color: var(--negative);
}
</style>
