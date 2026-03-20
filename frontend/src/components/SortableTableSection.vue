<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :eyebrow="eyebrow" :description="description">
        <span v-if="badge" class="pill">{{ badge }}</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <table v-if="sortedRows.length" class="simple-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">
              <button
                class="sort-button"
                type="button"
                @click="toggleSort(column.key)"
              >
                {{ column.label }}
                <span v-if="sortBy === column.key">{{ sortDirection === "asc" ? "↑" : "↓" }}</span>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in sortedRows" :key="rowKey ? String(row[rowKey]) : rowIndex">
            <td v-for="column in columns" :key="column.key">
              {{ formatCell(row[column.key]) }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import SectionHeader from "@/components/SectionHeader.vue";
import type { SortDirection, TableRow } from "@/utils/presentation";
import { sortRows } from "@/utils/presentation";

const props = defineProps<{
  title: string;
  columns: { key: string; label: string }[];
  rows: TableRow[];
  emptyMessage?: string;
  badge?: string;
  eyebrow?: string;
  description?: string;
  rowKey?: string;
  defaultSortBy?: string;
  defaultSortDirection?: SortDirection;
}>();

const sortBy = ref(props.defaultSortBy ?? props.columns[0]?.key ?? "");
const sortDirection = ref<SortDirection>(props.defaultSortDirection ?? "asc");

const sortedRows = computed(() =>
  sortBy.value ? sortRows(props.rows, sortBy.value, sortDirection.value) : props.rows,
);

function toggleSort(columnKey: string): void {
  if (sortBy.value === columnKey) {
    sortDirection.value = sortDirection.value === "asc" ? "desc" : "asc";
    return;
  }
  sortBy.value = columnKey;
  sortDirection.value = "asc";
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
</script>

<style scoped>
.sort-button {
  display: inline-flex;
  gap: 0.25rem;
  align-items: center;
  border: 0;
  padding: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
</style>
