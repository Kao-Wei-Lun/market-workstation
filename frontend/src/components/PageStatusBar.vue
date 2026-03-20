<template>
  <section class="panel status-panel">
    <div class="panel-body status-body">
      <div class="status-copy">
        <strong>{{ title }}</strong>
        <p v-if="hint" class="muted">{{ hint }}</p>
      </div>
      <div class="status-items">
        <span v-if="asOfDate" class="pill info">資料日期 {{ asOfDate }}</span>
        <span v-if="generatedAt" class="pill">更新時間 {{ generatedAt }}</span>
        <span v-if="itemCount !== undefined" class="pill">{{ itemCount }} 筆</span>
        <span v-if="demoHint" class="pill neutral">{{ demoHint }}</span>
        <button v-if="showRefresh" class="refresh-button" type="button" @click="$emit('refresh')">
          {{ refreshLabel || "重新整理" }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  asOfDate?: string | null;
  generatedAt?: string | null;
  itemCount?: number;
  hint?: string;
  demoHint?: string;
  showRefresh?: boolean;
  refreshLabel?: string;
}>();

defineEmits<{
  (event: "refresh"): void;
}>();
</script>

<style scoped>
.status-panel {
  border-style: dashed;
}

.status-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.status-copy {
  display: grid;
  gap: 0.25rem;
}

.status-copy strong,
.status-copy p {
  margin: 0;
}

.status-items {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.6rem;
}

.refresh-button {
  border: 1px solid var(--border);
  background: var(--panel-bg);
  border-radius: 999px;
  padding: 0.45rem 0.8rem;
  cursor: pointer;
}

@media (max-width: 960px) {
  .status-body {
    align-items: stretch;
    flex-direction: column;
  }

  .status-items {
    justify-content: flex-start;
  }
}
</style>
