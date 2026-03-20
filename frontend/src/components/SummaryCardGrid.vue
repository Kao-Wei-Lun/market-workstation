<template>
  <section class="summary-grid">
    <SummaryCard
      v-for="card in cards"
      :key="card.key"
      :card="card"
    />
  </section>
</template>

<script setup lang="ts">
import SummaryCard from "@/components/SummaryCard.vue";
import type { DashboardSummaryCard } from "@/types/dashboard";

defineProps<{
  cards: DashboardSummaryCard[];
}>();
</script>

<style scoped>
.summary-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
</style>
