<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="Dashboard"
      title="Reports"
      description="Latest generated reports, report bundle outputs, and report types ready for frontend display."
    />

    <FilterBar
      title="Report Explorer"
      description="Browse report bundles by date and focus on one section at a time."
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
            <option
              v-for="report in latestReports"
              :key="`${report.report_date}-${report.report_type}-${report.id}`"
              :value="report.report_date"
            >
              {{ formatDate(report.report_date) }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="report-type-filter">Report Type</label>
          <input id="report-type-filter" v-model="reportTypeFilter" placeholder="market_summary" />
        </div>
        <div class="field-group">
          <label for="report-section">Bundle Section</label>
          <select id="report-section" v-model="selectedSectionType">
            <option value="">First section</option>
            <option v-for="section in bundle?.sections ?? []" :key="section.section_type" :value="section.section_type">
              {{ section.title }}
            </option>
          </select>
        </div>
      </div>
    </FilterBar>

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

      <div class="page-section-grid">
        <DetailPanel title="Bundle Metadata" description="High-level context for the selected report bundle.">
          <MetricGrid :metrics="bundleMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="Report Type Mix"
          description="Counts of the latest visible report rows by report type."
          :points="reportTypeChartPoints"
          empty-message="No report mix available."
        />
      </div>

      <DetailPanel title="Report Highlights" description="Latest persisted report signals surfaced through the dashboard.">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="Latest Reports"
          description="Latest individual report rows returned by the report API."
          :columns="reportColumns"
          :rows="filteredReportRows"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="No reports available."
        />
      </div>

      <MarkdownSection
        v-if="selectedSection"
        title="Selected Bundle Section"
        :section-type="selectedSection.section_type"
        :description="selectedSection.title"
        :body="selectedSection.markdown_body"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchReportsDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchLatestReports, fetchReportBundle } from "@/api/reports";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MarkdownSection from "@/components/MarkdownSection.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageHeader from "@/components/PageHeader.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { DailyReportBundleContent } from "@/types/api";
import type { ReportDailyRead, ReportsDashboardRead } from "@/types/dashboard";
import { formatDate, formatNumber } from "@/utils/formatters";
import { filterRowsByQuery } from "@/utils/presentation";

const dashboard = ref<ReportsDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const reportTypeFilter = ref("");
const latestReports = ref<ReportDailyRead[]>([]);
const bundle = ref<DailyReportBundleContent | null>(null);
const selectedReportDate = ref("");
const selectedSectionType = ref("");

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

const filteredReportRows = computed(() => filterRowsByQuery(reportRows.value, ["type", "title"], reportTypeFilter.value));

const selectedSection = computed(() => {
  if (!bundle.value?.sections.length) {
    return null;
  }
  return (
    bundle.value.sections.find((section) => section.section_type === selectedSectionType.value) ??
    bundle.value.sections[0]
  );
});

const bundleMetrics = computed(() => {
  if (!bundle.value) {
    return [];
  }
  return [
    { label: "Bundle Version", value: bundle.value.metadata.bundle_version, hint: "content contract" },
    { label: "Section Count", value: formatNumber(bundle.value.metadata.section_count), hint: "renderable sections" },
    {
      label: "Top Candidates",
      value: bundle.value.metadata.top_candidate_symbols.join(", ") || "n/a",
      hint: "bundle metadata",
    },
    {
      label: "Strongest Group",
      value: bundle.value.metadata.strongest_group_name ?? "n/a",
      hint: "scanner highlight",
    },
  ];
});

const reportTypeChartPoints = computed(() => {
  const counts = new Map<string, number>();
  for (const report of latestReports.value) {
    counts.set(report.report_type, (counts.get(report.report_type) ?? 0) + 1);
  }
  return [...counts.entries()].map(([label, value]) => ({
    label,
    value,
    tone: "info" as const,
  }));
});

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
  selectedSectionType.value = bundle.value?.sections[0]?.section_type ?? "";
}

onMounted(loadReports);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
}
</style>
