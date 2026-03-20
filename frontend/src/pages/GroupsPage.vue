<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Groups"
      description="Tag-group dashboard for daily breadth, summary metrics, and ranked movers."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="group-tag">Tag</label>
          <input id="group-tag" v-model="tag" placeholder="semiconductor" />
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadGroup">Load group</button>
        </div>
      </div>
    </PageHeader>

    <LoadingState v-if="isLoading" message="Loading group dashboard..." />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No group data"
      message="Try another tag or load sample data first."
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

import { fetchGroupDashboard } from "@/api/dashboard";
import EmptyState from "@/components/EmptyState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { GroupDashboardRead } from "@/types/dashboard";

const tag = ref("semiconductor");
const dashboard = ref<GroupDashboardRead | null>(null);
const isLoading = ref(false);

async function loadGroup(): Promise<void> {
  isLoading.value = true;
  try {
    dashboard.value = await fetchGroupDashboard(tag.value);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadGroup);
</script>
