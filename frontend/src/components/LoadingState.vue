<template>
  <div class="state-box panel">
    <div class="panel-body">
      <strong>Loading...</strong>
      <p class="muted">{{ message }}</p>
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
</style>
