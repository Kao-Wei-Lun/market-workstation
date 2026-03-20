<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :eyebrow="eyebrow" :description="description">
        <slot name="header" />
      </SectionHeader>
    </div>
    <div class="panel-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import SectionHeader from "@/components/SectionHeader.vue";

defineProps<{
  title: string;
  description?: string;
  eyebrow?: string;
}>();
</script>
