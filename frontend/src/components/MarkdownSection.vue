<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description">
        <span v-if="sectionType" class="pill info">{{ sectionType }}</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <pre class="markdown-block">{{ body }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import SectionHeader from "@/components/SectionHeader.vue";

defineProps<{
  title: string;
  body: string;
  description?: string;
  sectionType?: string;
}>();
</script>

<style scoped>
.markdown-block {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.6;
}
</style>
