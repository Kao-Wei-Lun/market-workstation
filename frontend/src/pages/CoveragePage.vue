<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="管理"
      title="資料覆蓋"
      description="檢查目前資料範圍預設集、已載入標的、分類分布與本機初始化狀態。"
    />

    <FilterBar title="資料覆蓋篩選" description="切換預設集，查看目前本機資料覆蓋與初始化進度。">
      <div class="form-inline">
        <div class="field-group">
          <label for="coverage-preset">資料範圍預設集</label>
          <select id="coverage-preset" v-model="selectedPreset" @change="loadCoverage">
            <option v-for="preset in availablePresets" :key="preset" :value="preset">
              {{ preset }}
            </option>
          </select>
        </div>
        <div class="field-group">
          <label>&nbsp;</label>
          <button @click="loadCoverage">重新整理</button>
        </div>
      </div>
    </FilterBar>

    <PageStatusBar
      title="資料覆蓋狀態"
      :as-of-date="coverage?.data.completeness.reference_latest_date ?? null"
      :generated-at="formatDateTime(coverage?.meta.generated_at)"
      :item-count="coverage?.meta.item_count"
      hint="此頁顯示預設集定義與資料庫實際載入狀態的對照。"
      demo-hint="可先用 make list-universes 與 make load-universe 檢查範圍，再從任務中心或 demo-data 補齊缺資料。"
      :show-refresh="true"
      @refresh="loadCoverage"
    />

    <LoadingState v-if="isLoading" message="正在載入資料覆蓋狀態..." />
    <ErrorState
      v-else-if="errorMessage"
      title="資料覆蓋載入失敗"
      message="無法從後端取得 universe 與 coverage 狀態。"
      :detail="errorMessage"
    />
    <template v-else-if="coverage">
      <SummaryCardGrid :cards="coverage.summary_cards" />

      <DetailPanel title="資料覆蓋重點" description="快速檢查預設集與已載入資料的整體狀態。">
        <template #header>
          <span class="pill info">{{ coverage.data.preset.preset_name }}</span>
        </template>
        <ul class="highlights">
          <li v-for="item in coverage.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <MetricGrid :metrics="presetMetrics" />
        <MetricGrid :metrics="completenessMetrics" />
        <MiniBarChart
          title="市場別覆蓋"
          description="依 market 顯示目前已有資料的標的數。"
          :points="marketChartPoints"
          empty-message="目前沒有市場別統計。"
        />
        <MiniBarChart
          title="資產類型覆蓋"
          description="依 asset_type 顯示目前已載入的標的數。"
          :points="assetTypeChartPoints"
          empty-message="目前沒有資產類型統計。"
        />
      </div>

      <div class="page-section-grid">
        <SortableTableSection
          title="範圍區段"
          description="逐一檢視各區段的預設宣告、最新日期、缺資料與過期情況。"
          :columns="scopeColumns"
          :rows="scopeRows"
          default-sort-by="status_sort"
          default-sort-direction="desc"
          empty-message="目前沒有區段覆蓋資料。"
        />
        <SortableTableSection
          title="需補資料 / 補跑的區段"
          description="優先顯示缺資料、資料過期或僅部分完成 bootstrap 的 scope。"
          :columns="attentionColumns"
          :rows="attentionRows"
          default-sort-by="attention_score"
          default-sort-direction="desc"
          empty-message="目前所有 scope 都已就緒。"
        />
        <SortableTableSection
          title="市場統計"
          description="依市場別彙整標的數、最新日期與缺資料情況。"
          :columns="categoryColumns"
          :rows="marketRows"
          default-sort-by="instrument_count"
          default-sort-direction="desc"
          empty-message="目前沒有市場統計。"
        />
        <SortableTableSection
          title="資料來源統計"
          description="依 provider / source route 檢查目前本機已載入來源與資料完整度。"
          :columns="categoryColumns"
          :rows="sourceRouteRows"
          default-sort-by="instrument_count"
          default-sort-direction="desc"
          empty-message="目前沒有資料來源統計。"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { normalizeApiError } from "@/api/http";
import { fetchUniverseCoverage } from "@/api/system";
import DetailPanel from "@/components/DetailPanel.vue";
import ErrorState from "@/components/ErrorState.vue";
import FilterBar from "@/components/FilterBar.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid from "@/components/MetricGrid.vue";
import MiniBarChart from "@/components/MiniBarChart.vue";
import PageHeader from "@/components/PageHeader.vue";
import PageStatusBar from "@/components/PageStatusBar.vue";
import SortableTableSection from "@/components/SortableTableSection.vue";
import SummaryCardGrid from "@/components/SummaryCardGrid.vue";
import type { UniverseCoverageRead } from "@/types/system";
import { formatDate, formatDateTime, formatList, formatNumber } from "@/utils/formatters";

const coverage = ref<UniverseCoverageRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedPreset = ref("v1_market_expanded");
const route = useRoute();
const router = useRouter();

const scopeColumns = [
  { key: "scope", label: "區段" },
  { key: "group_label", label: "群組" },
  { key: "status", label: "狀態" },
  { key: "latest_data_date", label: "最新日期" },
  { key: "market", label: "市場" },
  { key: "asset_type", label: "資產類型" },
  { key: "with_data", label: "有資料" },
  { key: "missing_data", label: "缺資料" },
  { key: "stale_data", label: "過期" },
  { key: "loaded_instruments", label: "已載入標的" },
  { key: "configured_instruments", label: "預設標的" },
  { key: "watchlists", label: "觀察清單" },
  { key: "sample_symbols", label: "範例代號" },
];

const categoryColumns = [
  { key: "label", label: "分類" },
  { key: "instrument_count", label: "標的數" },
  { key: "with_data", label: "有資料" },
  { key: "missing", label: "缺資料" },
  { key: "stale", label: "過期" },
  { key: "latest_data_date", label: "最新日期" },
];

const attentionColumns = [
  { key: "scope", label: "區段" },
  { key: "status", label: "狀態" },
  { key: "latest_data_date", label: "最新日期" },
  { key: "missing_data", label: "缺資料" },
  { key: "stale_data", label: "過期" },
  { key: "action_hint", label: "建議動作" },
  { key: "sample_symbols", label: "樣本代號" },
];

const availablePresets = computed(() => coverage.value?.data.preset.available_presets ?? [selectedPreset.value]);

const presetMetrics = computed(() => {
  const preset = coverage.value?.data.preset;
  if (!preset) {
    return [];
  }
  return [
    { label: "預設集名稱", value: preset.preset_name, hint: "目前查詢對象" },
    { label: "宣告標的", value: formatNumber(preset.configured_instrument_count), hint: "config 內定義" },
    { label: "宣告清單", value: formatNumber(preset.configured_watchlist_count), hint: "預設觀察清單" },
    { label: "覆蓋區段", value: formatNumber(preset.scopes_declared), hint: "區段定義數" },
  ];
});

const completenessMetrics = computed(() => {
  const completeness = coverage.value?.data.completeness;
  if (!completeness) {
    return [];
  }
  return [
    { label: "參考最新日期", value: formatDate(completeness.reference_latest_date), hint: "coverage 基準日" },
    { label: "已 bootstrap 區段", value: formatNumber(completeness.bootstrapped_scope_count), hint: `共 ${completeness.scopes_declared} 個` },
    { label: "就緒區段", value: formatNumber(completeness.ready_scope_count), hint: "無缺資料且未過期" },
    { label: "需留意區段", value: formatNumber(completeness.attention_scope_count), hint: "可往下查看 scope 明細" },
    { label: "有資料標的", value: formatNumber(completeness.instruments_with_data_count), hint: "含日線或序列資料" },
    { label: "缺資料標的", value: formatNumber(completeness.missing_data_count), hint: "尚未載入或未產生資料" },
    { label: "過期標的", value: formatNumber(completeness.stale_data_count), hint: "最新日期落後基準日" },
    { label: "已載入標的", value: formatNumber(completeness.loaded_instrument_count), hint: `共宣告 ${completeness.configured_instrument_count} 筆` },
  ];
});

const marketChartPoints = computed(() =>
  (coverage.value?.data.market_counts ?? []).map((item) => ({
    label: item.label,
    value: item.instruments_with_data_count,
    tone: item.missing_data_count > 0 || item.stale_data_count > 0 ? ("negative" as const) : ("info" as const),
  })),
);

const assetTypeChartPoints = computed(() =>
  (coverage.value?.data.asset_type_counts ?? []).map((item) => ({
    label: item.label,
    value: item.instrument_count,
    tone: "positive" as const,
  })),
);

const scopeRows = computed(() =>
  (coverage.value?.data.scopes ?? []).map((scope) => ({
    scope: scope.label,
    group_label: scope.group_label,
    status: mapCoverageStatus(scope.status),
    status_sort: scope.status === "stale" ? 3 : scope.status === "missing" ? 2 : scope.status === "partial" ? 1 : 0,
    latest_data_date: formatDate(scope.latest_data_date),
    market: scope.market,
    asset_type: scope.asset_type,
    with_data: scope.instruments_with_data_count,
    missing_data: scope.missing_data_count,
    stale_data: scope.stale_data_count,
    loaded_instruments: scope.loaded_instrument_count,
    configured_instruments: scope.configured_instrument_count,
    watchlists: `${scope.loaded_watchlist_count}/${scope.configured_watchlist_count}`,
    sample_symbols: formatList(scope.sample_symbols, "無"),
  })),
);

const attentionRows = computed(() =>
  (coverage.value?.data.scopes ?? [])
    .filter((scope) => scope.status !== "ready")
    .map((scope) => ({
      scope: scope.label,
      status: mapCoverageStatus(scope.status),
      latest_data_date: formatDate(scope.latest_data_date),
      missing_data: scope.missing_data_count,
      stale_data: scope.stale_data_count,
      attention_score: scope.missing_data_count * 10 + scope.stale_data_count,
      action_hint: scope.status === "missing" ? "先 bootstrap / 補 ETL" : scope.status === "stale" ? "建議補跑資料" : "補齊缺漏標的",
      sample_symbols: formatList(
        scope.sample_missing_symbols.length > 0 ? scope.sample_missing_symbols : scope.sample_stale_symbols,
        "無",
      ),
    })),
);

const marketRows = computed(() =>
  (coverage.value?.data.market_counts ?? []).map((item) => ({
    label: item.label,
    instrument_count: item.instrument_count,
    with_data: item.instruments_with_data_count,
    missing: item.missing_data_count,
    stale: item.stale_data_count,
    latest_data_date: formatDate(item.latest_data_date),
  })),
);

const sourceRouteRows = computed(() =>
  (coverage.value?.data.source_route_counts ?? []).map((item) => ({
    label: item.label,
    instrument_count: item.instrument_count,
    with_data: item.instruments_with_data_count,
    missing: item.missing_data_count,
    stale: item.stale_data_count,
    latest_data_date: formatDate(item.latest_data_date),
  })),
);

function mapCoverageStatus(status: UniverseCoverageRead["data"]["scopes"][number]["status"]): string {
  if (status === "ready") return "就緒";
  if (status === "partial") return "部分完成";
  if (status === "stale") return "資料過期";
  return "缺資料";
}

async function loadCoverage(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    coverage.value = await fetchUniverseCoverage(selectedPreset.value);
    await router.replace({ query: { preset: selectedPreset.value || undefined } });
  } catch (error) {
    errorMessage.value = normalizeApiError(error).detail;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  selectedPreset.value = typeof route.query.preset === "string" ? route.query.preset : selectedPreset.value;
  await loadCoverage();
});
</script>
