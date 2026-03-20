<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description" />
    </div>
    <div class="panel-body">
      <div v-if="sections.length" class="section-nav-list">
        <button
          v-for="section in sections"
          :key="section.key"
          class="section-nav-item"
          :class="{ active: section.key === selectedKey }"
          type="button"
          @click="$emit('select', section.key)"
        >
          <div class="section-nav-copy">
            <strong>{{ section.title }}</strong>
            <span class="muted">{{ section.sectionType }}</span>
          </div>
          <div class="section-nav-meta">
            <span class="pill">{{ section.markdownLineCount }} 行</span>
            <span class="pill info">{{ section.payloadFieldCount }} 欄</span>
            <span class="pill neutral">{{ section.relatedLinkCount }} 導頁</span>
          </div>
        </button>
      </div>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import SectionHeader from "@/components/SectionHeader.vue";
import type { ReportSectionSummaryItem } from "@/utils/reports";

withDefaults(
  defineProps<{
    title: string;
    sections: ReportSectionSummaryItem[];
    selectedKey?: string;
    description?: string;
    emptyMessage?: string;
  }>(),
  {
    selectedKey: "",
    description: undefined,
    emptyMessage: "目前沒有可切換的區塊。",
  },
);

defineEmits<{
  (event: "select", key: string): void;
}>();
</script>

<style scoped>
.section-nav-list {
  display: grid;
  gap: 0.75rem;
}

.section-nav-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.8rem 0.95rem;
  text-align: left;
  cursor: pointer;
}

.section-nav-item.active {
  border-color: var(--accent);
  background: rgba(22, 89, 146, 0.08);
}

.section-nav-copy {
  display: grid;
  gap: 0.2rem;
}

.section-nav-copy strong,
.section-nav-copy span {
  margin: 0;
}

.section-nav-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

@media (max-width: 960px) {
  .section-nav-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .section-nav-meta {
    justify-content: flex-start;
  }
}
</style>
