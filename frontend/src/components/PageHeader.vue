<template>
  <div class="page-header">
    <div>
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p class="muted">{{ description }}</p>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { t } from "@/utils/locale";

const props = defineProps<{
  title: string;
  description: string;
  eyebrow?: string;
}>();

const title = computed(() => t(props.title));
const description = computed(() => t(props.description));
const eyebrow = computed(() => (props.eyebrow ? t(props.eyebrow) : ""));
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.page-header h1 {
  margin: 0.1rem 0 0.35rem;
  font-size: 1.6rem;
}

.page-header p {
  margin: 0;
}

.eyebrow {
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
</style>
