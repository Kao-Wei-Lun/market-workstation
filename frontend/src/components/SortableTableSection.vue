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
          <tr
            v-for="(row, rowIndex) in sortedRows"
            :key="rowKey ? String(row[rowKey]) : rowIndex"
            :class="{ interactive: interactiveRows, selected: isSelectedRow(row) }"
            @click="handleRowClick(row)"
          >
            <td v-for="column in columns" :key="column.key">
              <RouterLink
                v-if="getLinkedCell(row[column.key])"
                :to="getLinkedCell(row[column.key])!.to"
                class="table-link"
                @click.stop
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
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";

import SectionHeader from "@/components/SectionHeader.vue";
import type { SortDirection, TableRow } from "@/utils/presentation";
import { isLinkedCellValue, sortRows } from "@/utils/presentation";

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
  selectedRowKey?: string | number | null;
  interactiveRows?: boolean;
}>();

const emit = defineEmits<{
  (event: "row-select", row: TableRow): void;
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

function isSelectedRow(row: TableRow): boolean {
  if (!props.rowKey || props.selectedRowKey === null || props.selectedRowKey === undefined) {
    return false;
  }
  return String(row[props.rowKey]) === String(props.selectedRowKey);
}

function handleRowClick(row: TableRow): void {
  if (!props.interactiveRows) {
    return;
  }
  emit("row-select", row);
}

function getLinkedCell(value: unknown) {
  return isLinkedCellValue(value) ? value : null;
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

tbody tr.interactive {
  cursor: pointer;
}

tbody tr.interactive:hover {
  background: rgba(22, 89, 146, 0.06);
}

tbody tr.selected {
  background: rgba(22, 89, 146, 0.1);
}

.table-link {
  color: var(--accent);
  text-decoration: none;
}

.table-link:hover {
  text-decoration: underline;
}
</style>
