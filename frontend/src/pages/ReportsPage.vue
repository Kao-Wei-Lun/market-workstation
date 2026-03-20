<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Reports"
      description="Latest generated reports, report bundle outputs, and report types ready for frontend display."
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="report-limit">Limit</label>
          <select id="report-limit" v-model="limit" @change="loadReports">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </div>
        <div class="field-group">
          <label for="report-date">Bundle Date</label>
          <select id="report-date" v-model="selectedReportDate" @change="loadSelectedBundle">
            <option value="">Latest</option>
            <option v-for="report in latestReports" :key="`${report.report_date}-${report.report_type}-${report.id}`" :value="report.report_date">
              {{ formatDate(report.report_date) }}
            </option>
          </select>
        </div>
      </div>
    </PageHeader>

    <LoadingState v-if="isLoading" message="Loading reports dashboard..." />
    <ErrorState
      v-else-if="errorMessage"
      title="Report request failed"
      message="The latest reports or report bundle could not be loaded."
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="No reports available"
      message="The backend has no persisted daily reports yet. Run make demo-data to generate a repeatable local report bundle."
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />
      <section class="panel">
        <div class="panel-header">
          <SectionHeader title="Report Highlights" description="Latest persisted report signals surfaced through the dashboard." />
        </div>
        <div class="panel-body">
          <ul class="highlights">
            <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
          </ul>
        </div>
      </section>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <TableSection
          title="Latest Reports"
          description="Latest individual report rows returned by the report API."
          :columns="reportColumns"
          :rows="reportRows"
          empty-message="No reports available."
        />
      </div>

      <section class="panel" v-if="bundle">
        <div class="panel-header">
          <SectionHeader
            title="Daily Report Bundle"
            :description="`Bundle version ${bundle.metadata.bundle_version} with ${bundle.metadata.section_count} sections.`"
          >
            <span class="pill info">{{ bundle.report_date }}</span>
          </SectionHeader>
        </div>
        <div class="panel-body report-section-stack">
          <article v-for="section in bundle.sections" :key="section.section_type" class="report-section">
            <h3>{{ section.title }}</h3>
            <p class="muted">{{ section.section_type }}</p>
            <pre class="markdown-preview">{{ section.markdown_body }}</pre>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchReportsDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchLatestReports, fetchReportBundle } from "@/api/reports";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SectionHeader from "@/components/SectionHeader.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import TableSection from "@/components/TableSection.vue";
import type { DailyReportBundleContent } from "@/types/api";
import type { ReportDailyRead, ReportsDashboardRead } from "@/types/dashboard";
import { formatDate } from "@/utils/formatters";

const dashboard = ref<ReportsDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const latestReports = ref<ReportDailyRead[]>([]);
const bundle = ref<DailyReportBundleContent | null>(null);
const selectedReportDate = ref("");

const reportColumns = [
  { key: "date", label: "Date" },
  { key: "type", label: "Type" },
  { key: "title", label: "Title" },
];

const reportRows = computed(() =>
  latestReports.value.map((report) => ({
    date: formatDate(report.report_date),
    type: report.report_type,
    title: report.title,
  })),
);

async function loadReports(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const [dashboardResponse, latestReportsResponse] = await Promise.all([
      fetchReportsDashboard({ limit: limit.value }),
      fetchLatestReports({ limit: limit.value }),
    ]);
    dashboard.value = dashboardResponse;
    latestReports.value = latestReportsResponse;
    selectedReportDate.value = latestReportsResponse[0]?.report_date ?? dashboardResponse.meta.as_of_date ?? "";
    await loadSelectedBundle();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedBundle(): Promise<void> {
  bundle.value = selectedReportDate.value ? await fetchReportBundle(selectedReportDate.value) : null;
}

onMounted(loadReports);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
}

.report-section-stack {
  display: grid;
  gap: 1rem;
}

.report-section {
  padding: 1rem;
  border-radius: 16px;
  background: var(--panel-alt);
}

.report-section h3,
.report-section p {
  margin: 0 0 0.35rem;
}

.markdown-preview {
  margin: 0.5rem 0 0;
  white-space: pre-wrap;
  font-family: inherit;
}
</style>
