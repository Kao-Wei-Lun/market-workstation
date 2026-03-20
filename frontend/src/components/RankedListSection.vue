<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="list.title" :description="list.key">
        <span class="pill">{{ list.item_count }} 筆</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <table class="simple-table" v-if="list.items.length">
        <thead>
          <tr>
            <th>{{ t("Label") }}</th>
            <th>{{ t("Primary") }}</th>
            <th>{{ t("Secondary") }}</th>
            <th>{{ t("Hint") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list.items" :key="item.key">
            <td>
              <RouterLink v-if="getItemLink?.(item)" :to="getItemLink(item)!" class="table-link">
                {{ t(item.label) }}
              </RouterLink>
              <template v-else>
                {{ t(item.label) }}
              </template>
            </td>
            <td>{{ item.primary_value }}</td>
            <td>{{ item.secondary_value ?? "無資料" }}</td>
            <td>{{ item.hint ? t(item.hint) : "無資料" }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">目前沒有可顯示的資料。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router";

import SectionHeader from "@/components/SectionHeader.vue";
import type { DashboardRankedItem, DashboardRankedList } from "@/types/dashboard";
import { t } from "@/utils/locale";

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
