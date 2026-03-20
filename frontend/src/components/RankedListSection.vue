<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="list.title" :description="list.key">
        <span class="pill">{{ list.item_count }} items</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <table class="simple-table" v-if="list.items.length">
        <thead>
          <tr>
            <th>Label</th>
            <th>Primary</th>
            <th>Secondary</th>
            <th>Hint</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list.items" :key="item.key">
            <td>
              <RouterLink v-if="getItemLink?.(item)" :to="getItemLink(item)!" class="table-link">
                {{ item.label }}
              </RouterLink>
              <template v-else>
                {{ item.label }}
              </template>
            </td>
            <td>{{ item.primary_value }}</td>
            <td>{{ item.secondary_value ?? "n/a" }}</td>
            <td>{{ item.hint ?? "n/a" }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">No items available.</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router";

import SectionHeader from "@/components/SectionHeader.vue";
import type { DashboardRankedItem, DashboardRankedList } from "@/types/dashboard";

defineProps<{
  list: DashboardRankedList;
  getItemLink?: (item: DashboardRankedItem) => RouteLocationRaw | null;
}>();
</script>

<style scoped>
.table-link {
  color: var(--accent);
  text-decoration: none;
}

.table-link:hover {
  text-decoration: underline;
}
</style>
