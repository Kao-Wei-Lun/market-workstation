<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Candidates"
      description="Next-day watch candidates ranked from the backend scoring and scanner context."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="candidate-limit">Limit</label>
          <select id="candidate-limit" v-model="limit" @change="loadCandidates">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </div>
      </div>
    </PageHeader>

    <LoadingState v-if="isLoading" message="Loading candidate dashboard..." />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No candidate data"
      message="Generate a candidate run from the backend or sample workflow."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />
      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchCandidatesDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { CandidatesDashboardRead } from "@/types/dashboard";

const dashboard = ref<CandidatesDashboardRead | null>(null);
const isLoading = ref(false);
const limit = ref(10);

async function loadCandidates(): Promise<void> {
  isLoading.value = true;
  try {
    dashboard.value = await fetchCandidatesDashboard({ limit: limit.value });
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadCandidates);
</script>
