<template>
  <section class="panel">
    <div class="panel-header">
      <h2>{{ list.title }}</h2>
      <span class="pill">{{ list.item_count }} items</span>
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
            <td>{{ item.label }}</td>
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
import type { DashboardRankedList } from "@/types/dashboard";

defineProps<{
  list: DashboardRankedList;
}>();
</script>
