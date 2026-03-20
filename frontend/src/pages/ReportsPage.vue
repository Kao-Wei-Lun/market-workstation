<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="儀表板"
      title="報表"
      description="查看最新生成的日報、報表彙整區塊與前端可直接呈現的報表內容。"
    />

    <FilterBar
      title="報表探索"
      description="依日期瀏覽報表彙整內容，並聚焦單一區塊。"
    >
      <div class="form-inline">
        <div class="field-group">
          <label for="report-limit">筆數</label>
          <select id="report-limit" v-model="limit" @change="loadReports">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </div>
        <div class="field-group">
          <label for="report-date">報表日期</label>
          <input id="report-date" v-model="selectedReportDate" type="date" @change="loadReports" />
        </div>
        <div class="field-group">
          <label for="report-type-filter">報表類型</label>
          <select id="report-type-filter" v-model="reportTypeFilter" @change="loadReports">
            <option value="">全部類型</option>
            <option v-for="reportType in availableReportTypes" :key="reportType" :value="reportType">
              {{ reportType }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label for="report-search">搜尋</label>
          <input id="report-search" v-model="searchQuery" placeholder="標題、類型、內容關鍵字" />
        </div>
        <div class="field-group">
          <label for="report-section">報表區塊</label>
          <select id="report-section" v-model="selectedSectionType">
            <option value="">第一個區塊</option>
            <option v-for="section in bundle?.sections ?? []" :key="section.section_type" :value="section.section_type">
              {{ section.title }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadReports">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <DetailPanel title="常用日期" description="快速切換近期有資料的報表日期。">
      <div v-if="availableReportDates.length" class="quick-date-list">
        <button
          v-for="reportDate in availableReportDates"
          :key="reportDate"
          class="quick-date-button"
          :class="{ active: selectedReportDate === reportDate }"
          type="button"
          @click="selectReportDate(reportDate)"
        >
          {{ formatDate(reportDate) }}
        </button>
      </div>
      <p v-else class="muted">目前沒有可快速切換的報表日期。</p>
    </DetailPanel>

    <PageStatusBar
      title="報表資料狀態"
      :as-of-date="dashboard?.meta.as_of_date ?? null"
      :generated-at="formatDateTime(dashboard?.meta.generated_at)"
      :item-count="dashboard?.meta.item_count"
      hint="報表頁整合 bundle 區塊、markdown 內容與單筆報表列。"
      demo-hint="若尚無報表資料，請執行 make demo-data 產生示範報表彙整。"
      :show-refresh="true"
      @refresh="loadReports"
    />

    <LoadingState v-if="isLoading" message="正在載入報表..." />
    <ErrorState
      v-else-if="errorMessage"
      title="報表載入失敗"
      message="無法載入最新報表或報表 bundle。"
      :detail="errorMessage"
    />
    <EmptyState
      v-else-if="dashboard?.meta.is_empty"
      title="尚無報表資料"
      message="後端目前還沒有保存的日報。執行 make demo-data 後即可產生可重複的本機報表彙整。"
    />
    <template v-else-if="dashboard">
      <SummaryCardGrid :cards="dashboard.summary_cards" />

      <div class="page-section-grid">
        <DetailPanel title="報表彙整資訊" description="顯示目前報表彙整內容的整體脈絡。">
          <template #header>
            <PillList :items="bundlePills" empty-message="目前沒有報表彙整標籤。" />
          </template>
          <MetricGrid :metrics="bundleMetrics" />
        </DetailPanel>
        <MiniBarChart
          title="報表類型分布"
          description="統計目前可見報表列的類型分布。"
          :points="reportTypeChartPoints"
          empty-message="目前沒有報表分布資料。"
        />
      </div>

      <DetailPanel title="報表重點" description="整理目前儀表板中最重要的報表觀察。">
        <ul class="highlights">
          <li v-for="item in dashboard.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <RankedListSection v-for="list in dashboard.ranked_lists" :key="list.key" :list="list" />
        <SortableTableSection
          title="近期報表"
          description="顯示報表 API 回傳的近期單筆報表。"
          :columns="reportColumns"
          :rows="filteredReportRows"
          row-key="report_key"
          :selected-row-key="selectedReportRowKey"
          :interactive-rows="true"
          @row-select="handleReportRowSelect"
          default-sort-by="date"
          default-sort-direction="desc"
          empty-message="目前沒有報表資料。"
        />
      </div>

      <DetailPanel v-if="selectedReport" title="報表列明細" description="檢視已保存報表的中繼資訊與摘要內容。">
        <template #header>
          <PillList :items="reportRelatedPills" empty-message="目前沒有相關導頁。" />
        </template>
        <MetricGrid :metrics="selectedReportMetrics" />
      </DetailPanel>

      <MarkdownSection
        v-if="selectedReport"
        title="已保存報表內容"
        :description="selectedReport.title"
        :body="selectedReport.markdown_text"
      />

      <DetailPanel
        v-if="selectedSection"
        title="區塊摘要"
        description="顯示目前區塊的欄位規模、閱讀密度與可延伸查看的導頁。"
      >
        <template #header>
          <PillList :items="reportRelatedPills" empty-message="目前沒有相關導頁。" />
        </template>
        <MetricGrid :metrics="selectedSectionMetrics" />
      </DetailPanel>

      <EmptyState
        v-else-if="selectedReportDate"
        title="該日期尚無報表彙整"
        message="目前找不到此日期的報表彙整。請切換日期或先重新產生日報。"
      />

      <div v-if="selectedSection" class="page-section-grid">
        <ReportSectionNavigator
          title="區塊導覽"
          description="快速切換報表彙整內的重點區塊，方便逐段閱讀日報。"
          :sections="sectionSummaries"
          :selected-key="selectedSection.section_type"
          @select="handleSectionSelect"
        />
        <MarkdownSection
          title="目前報表區塊"
          :section-type="selectedSection.section_type"
          :description="selectedSection.title"
          :body="selectedSection.markdown_body"
        />
        <StructuredPayloadSection
          title="區塊結構化內容"
          description="顯示 section payload，方便前端實作與資料核對。"
          :payload="selectedSection.payload_json"
          :resolve-link="resolveStructuredPayloadLink"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { RouteLocationRaw } from "vue-router";

import { fetchReportsDashboard } from "@/api/dashboard";
import { normalizeApiError } from "@/api/http";
import { fetchReportBundle, fetchReports } from "@/api/reports";
import DetailPanel from "@/components/DetailPanel.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MarkdownSection from "@/components/MarkdownSection.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import PageHeader from "@/components/PageHeader.vue";
import PillList from "@/components/PillList.vue";
import RankedListSection from "@/components/RankedListSection.vue";
import ReportSectionNavigator from "@/components/ReportSectionNavigator.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import StructuredPayloadSection from "@/components/StructuredPayloadSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { DailyReportBundleContent } from "@/types/api";
import type { ReportDailyRead, ReportsDashboardRead } from "@/types/dashboard";
import { formatDate, formatDateTime, formatList, formatNumber } from "@/utils/formatters";
import {
  buildReportRelatedLinks,
  buildReportRowRelatedLinks,
  buildReportSectionMetrics,
  buildReportSectionSummaries,
  listAvailableReportDates,
  listAvailableReportTypes,
} from "@/utils/reports";
import type { TableRow } from "@/utils/presentation";
import { filterRowsByQuery, makeLinkedCell } from "@/utils/presentation";

const dashboard = ref<ReportsDashboardRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const limit = ref(10);
const reportTypeFilter = ref("");
const searchQuery = ref("");
const latestReports = ref<ReportDailyRead[]>([]);
const bundle = ref<DailyReportBundleContent | null>(null);
const selectedReportDate = ref("");
const selectedSectionType = ref("");
const selectedReportId = ref<number | null>(null);
const route = useRoute();
const router = useRouter();

const reportColumns = [
  { key: "date", label: "日期" },
  { key: "type", label: "類型" },
  { key: "title", label: "標題" },
];

const reportRows = computed(() =>
  latestReports.value.map((report) => ({
    report_key: report.id,
    date: formatDate(report.report_date),
    type: report.report_type,
    title: makeLinkedCell(report.title, {
      name: "reports",
      query: {
        reportDate: report.report_date,
        reportType: report.report_type,
      },
    }),
  })),
);

const filteredReportRows = computed(() => filterRowsByQuery(reportRows.value, ["type", "title"], searchQuery.value));

const selectedSection = computed(() => {
  if (!bundle.value?.sections.length) {
    return null;
  }
  return (
    bundle.value.sections.find((section) => section.section_type === selectedSectionType.value) ??
    bundle.value.sections[0]
  );
});

const selectedReport = computed(() => latestReports.value.find((report) => report.id === selectedReportId.value) ?? null);
const selectedReportRowKey = computed(() => (selectedReportId.value ? String(selectedReportId.value) : null));
const availableReportDates = computed(() =>
  listAvailableReportDates(dashboard.value?.data?.reports?.length ? dashboard.value.data.reports : latestReports.value),
);
const availableReportTypes = computed(() => listAvailableReportTypes(latestReports.value));
const reportRelatedLinks = computed(() => buildReportRelatedLinks(bundle.value, selectedSection.value));
const reportRowRelatedLinks = computed(() => buildReportRowRelatedLinks(selectedReport.value, selectedReportDate.value));
const sectionSummaries = computed(() => buildReportSectionSummaries(bundle.value));
const selectedSectionMetrics = computed(() =>
  buildReportSectionMetrics(bundle.value, selectedSection.value, reportRelatedLinks.value.length),
);

const reportRelatedPills = computed(() =>
  [...reportRelatedLinks.value, ...reportRowRelatedLinks.value].map((link) => ({
    label: link.label,
    to: link.to,
    tone: "info",
  })),
);

const bundleMetrics = computed(() => {
  if (!bundle.value) {
    return [];
  }
  return [
    { label: "彙整版本", value: bundle.value.metadata.bundle_version, hint: "內容契約" },
    { label: "區塊數", value: formatNumber(bundle.value.metadata.section_count), hint: "可顯示區塊" },
    {
      label: "高分候選",
      value: formatList(bundle.value.metadata.top_candidate_symbols, "無資料"),
      hint: "彙整中繼資訊",
    },
    {
      label: "最強群組",
      value: bundle.value.metadata.strongest_group_name ?? "無資料",
      hint: "掃描重點",
    },
    {
      label: "最強清單",
      value: bundle.value.metadata.strongest_watchlist_name ?? "無資料",
      hint: "watchlist 脈絡",
    },
  ];
});

const bundlePills = computed(() => {
  if (!bundle.value) {
    return [];
  }
  return [
    { label: `報表日期 ${formatDate(bundle.value.report_date)}`, tone: "info" },
    { label: `版本 ${bundle.value.metadata.bundle_version}` },
    ...bundle.value.metadata.top_candidate_symbols.slice(0, 3).map((symbol) => ({
      label: `候選 ${symbol}`,
      to: { name: "candidates", query: { candidateDate: bundle.value?.report_date, search: symbol } },
      tone: "info",
    })),
  ];
});

const selectedReportMetrics = computed(() => {
  if (!selectedReport.value) {
    return [];
  }
  return [
    { label: "類型", value: selectedReport.value.report_type, hint: "報表列類型" },
    { label: "鍵值", value: selectedReport.value.report_key, hint: "報表 key" },
    { label: "日期", value: formatDate(selectedReport.value.report_date), hint: "報表日期" },
    { label: "建立時間", value: formatDateTime(selectedReport.value.created_at), hint: "資料寫入時間" },
    { label: "內容摘要", value: selectedReport.value.markdown_text.slice(0, 120) || "無資料", hint: "內容預覽" },
    { label: "結構欄位", value: formatNumber(Object.keys(selectedReport.value.content_json ?? {}).length), hint: "content_json 欄位數" },
  ];
});

function handleReportRowSelect(row: TableRow): void {
  selectedReportId.value = Number(row.report_key);
}

function handleSectionSelect(sectionType: string): void {
  selectedSectionType.value = sectionType;
}

function selectReportDate(reportDate: string): void {
  selectedReportDate.value = reportDate;
  void loadReports();
}

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
      fetchReports({
        reportDate: selectedReportDate.value || undefined,
        reportType: reportTypeFilter.value || undefined,
        limit: limit.value,
      }),
    ]);
    dashboard.value = dashboardResponse;
    latestReports.value = latestReportsResponse;
    selectedReportDate.value = selectedReportDate.value || latestReportsResponse[0]?.report_date || dashboardResponse.meta.as_of_date || "";
    await loadSelectedBundle();
    selectedReportId.value = selectedReportId.value ?? latestReportsResponse[0]?.id ?? null;
    syncRouteQuery();
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

async function loadSelectedBundle(): Promise<void> {
  bundle.value = selectedReportDate.value ? await fetchReportBundle(selectedReportDate.value) : null;
  selectedSectionType.value = selectedSectionType.value || bundle.value?.sections[0]?.section_type || "";
}

function syncRouteQuery(): void {
  void router.replace({
    query: {
      limit: String(limit.value),
      reportDate: selectedReportDate.value || undefined,
      reportType: reportTypeFilter.value || undefined,
      search: searchQuery.value || undefined,
      section: selectedSectionType.value || undefined,
    },
  });
}

function resolveStructuredPayloadLink(key: string, value: unknown): { label: string; to: RouteLocationRaw } | null {
  if (typeof value !== "string" && typeof value !== "number") {
    return null;
  }

  const normalizedKey = key.toLowerCase();
  const stringValue = String(value);

  if (normalizedKey === "tag" || normalizedKey.endsWith("_group_name")) {
    return {
      label: stringValue,
      to: { name: "groups", query: { tag: stringValue, tradeDate: selectedReportDate.value || undefined } },
    };
  }

  if (normalizedKey === "watchlist_id") {
    return {
      label: `觀察清單 ${stringValue}`,
      to: { name: "watchlists", query: { watchlistId: stringValue, tradeDate: selectedReportDate.value || undefined } },
    };
  }

  if (normalizedKey.includes("symbol")) {
    return {
      label: stringValue,
      to: { name: "candidates", query: { search: stringValue, candidateDate: selectedReportDate.value || undefined } },
    };
  }

  if (normalizedKey === "top_candidate_symbols" || normalizedKey === "candidate_symbols") {
    return {
      label: stringValue,
      to: { name: "candidates", query: { search: stringValue, candidateDate: selectedReportDate.value || undefined } },
    };
  }

  return null;
}

onMounted(() => {
  limit.value = typeof route.query.limit === "string" ? Number(route.query.limit) : 10;
  selectedReportDate.value = typeof route.query.reportDate === "string" ? route.query.reportDate : "";
  reportTypeFilter.value = typeof route.query.reportType === "string" ? route.query.reportType : "";
  searchQuery.value = typeof route.query.search === "string" ? route.query.search : "";
  selectedSectionType.value = typeof route.query.section === "string" ? route.query.section : "";
  return loadReports();
});

watch([reportTypeFilter, searchQuery, selectedSectionType, selectedReportDate], syncRouteQuery);
</script>

<style scoped>
.highlights {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.5rem;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.detail-link {
  color: var(--accent);
  text-decoration: none;
}

.detail-link:hover {
  text-decoration: underline;
}

.quick-date-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.quick-date-button {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--panel-bg);
  padding: 0.5rem 0.9rem;
  cursor: pointer;
}

.quick-date-button.active {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(22, 89, 146, 0.08);
}
</style>
