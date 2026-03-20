<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description">
        <span v-if="sectionType" class="pill info">{{ sectionType }}</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <div v-if="blocks.length" class="markdown-flow">
        <template v-for="block in blocks" :key="block.key">
          <h3 v-if="block.type === 'heading'" :class="['markdown-heading', `level-${block.level}`]">
            {{ block.text }}
          </h3>
          <p v-else-if="block.type === 'paragraph'" class="markdown-paragraph">
            {{ block.text }}
          </p>
          <ul v-else class="markdown-list">
            <li v-for="item in block.items" :key="item">{{ item }}</li>
          </ul>
        </template>
      </div>
      <p v-else class="muted">目前沒有可顯示的內容。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import SectionHeader from "@/components/SectionHeader.vue";
import { parseMarkdownBlocks } from "@/utils/markdown";

const props = defineProps<{
  title: string;
  body: string;
  description?: string;
  sectionType?: string;
}>();

const blocks = computed(() => parseMarkdownBlocks(props.body));
</script>

<style scoped>
.markdown-flow {
  display: grid;
  gap: 0.75rem;
}

.markdown-heading,
.markdown-paragraph,
.markdown-list {
  margin: 0;
}

.markdown-heading {
  color: var(--accent);
  font-size: 1rem;
}

.markdown-heading.level-2 {
  font-size: 0.95rem;
}

.markdown-heading.level-3 {
  font-size: 0.9rem;
}

.markdown-paragraph {
  line-height: 1.6;
}

.markdown-list {
  padding-left: 1.1rem;
  line-height: 1.6;
}
</style>
