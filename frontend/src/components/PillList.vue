<template>
  <div v-if="normalizedItems.length" class="pill-list">
    <template v-for="item in normalizedItems" :key="item.key">
      <RouterLink v-if="item.to" :to="item.to" class="pill pill-link" :class="item.tone">
        {{ item.label }}
      </RouterLink>
      <span v-else class="pill" :class="item.tone">{{ item.label }}</span>
    </template>
  </div>
  <p v-else class="muted">{{ emptyMessage }}</p>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";

interface PillItem {
  label: string;
  to?: RouteLocationRaw | null;
  tone?: string;
}

const props = withDefaults(
  defineProps<{
    items: Array<string | PillItem>;
    emptyMessage?: string;
  }>(),
  {
    emptyMessage: "目前沒有可顯示的項目。",
  },
);

const normalizedItems = computed(() =>
  props.items.map((item, index) => {
    if (typeof item === "string") {
      return { key: `${item}-${index}`, label: item, to: null, tone: "" };
    }
    return {
      key: `${item.label}-${index}`,
      label: item.label,
      to: item.to ?? null,
      tone: item.tone ?? "",
    };
  }),
);
</script>

<style scoped>
.pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.pill-link {
  text-decoration: none;
}

.pill-link:hover {
  text-decoration: underline;
}
</style>
