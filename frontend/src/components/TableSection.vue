<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :eyebrow="eyebrow" :description="description">
        <span v-if="badge" class="pill">{{ badge }}</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <table v-if="rows.length" class="simple-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in rows" :key="rowKey ? String(row[rowKey]) : rowIndex">
            <td v-for="column in columns" :key="column.key">
              <RouterLink
                v-if="getLinkedCell(row[column.key])"
                :to="getLinkedCell(row[column.key])!.to"
                class="table-link"
              >
                {{ getLinkedCell(row[column.key])!.label }}
              </RouterLink>
              <template v-else>
                {{ formatCell(row[column.key]) }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";

import SectionHeader from "@/components/SectionHeader.vue";
import { isLinkedCellValue } from "@/utils/presentation";

type TableRow = Record<string, unknown>;

defineProps<{
  title: string;
  columns: { key: string; label: string }[];
  rows: TableRow[];
  emptyMessage?: string;
  badge?: string;
  eyebrow?: string;
  description?: string;
  rowKey?: string;
}>();

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "無資料";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function getLinkedCell(value: unknown) {
  return isLinkedCellValue(value) ? value : null;
}
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
