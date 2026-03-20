<template>
  <div class="page-grid">
    <PageHeader
      eyebrow="管理"
      title="資料覆蓋"
      description="檢查目前 universe preset、已載入標的、分類分布與本機 bootstrap 狀態。"
    />

    <FilterBar title="Coverage 篩選" description="切換 preset，查看目前本機資料覆蓋與 bootstrap 進度。">
      <div class="form-inline">
        <div class="field-group">
          <label for="coverage-preset">Universe preset</label>
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
      title="Coverage 狀態"
      :generated-at="formatDateTime(coverage?.meta.generated_at)"
      :item-count="coverage?.meta.item_count"
      hint="此頁顯示 config preset 與資料庫實際載入狀態的對照。"
      demo-hint="可先用 make list-universes 與 make load-universe 檢查或補齊 universe。"
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

      <DetailPanel title="Coverage 重點" description="快速檢查 preset 與已載入資料的整體狀態。">
        <template #header>
          <span class="pill info">{{ coverage.data.preset.preset_name }}</span>
        </template>
        <ul class="highlights">
          <li v-for="item in coverage.highlights" :key="item">{{ item }}</li>
        </ul>
      </DetailPanel>

      <div class="page-section-grid">
        <MetricGrid :metrics="presetMetrics" />
        <MiniBarChart
          title="市場別覆蓋"
          description="依 market 顯示目前已載入的標的數。"
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
          title="Universe 區段"
          description="逐一檢視各 scope 的 preset 宣告與已載入進度。"
          :columns="scopeColumns"
          :rows="scopeRows"
          default-sort-by="loaded_instruments"
          default-sort-direction="desc"
          empty-message="目前沒有 scope coverage 資料。"
        />
        <SortableTableSection
          title="Market 統計"
          description="依市場別彙整目前資料庫中已啟用標的數。"
          :columns="categoryColumns"
          :rows="marketRows"
          default-sort-by="instrument_count"
          default-sort-direction="desc"
          empty-message="目前沒有 market 統計。"
        />
        <SortableTableSection
          title="資料來源統計"
          description="依 provider/source route 檢查目前本機已載入來源。"
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
import { formatDateTime, formatList, formatNumber } from "@/utils/formatters";

const coverage = ref<UniverseCoverageRead | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedPreset = ref("v1_market_expanded");
const route = useRoute();
const router = useRouter();

const scopeColumns = [
  { key: "scope", label: "區段" },
  { key: "market", label: "市場" },
  { key: "asset_type", label: "資產類型" },
  { key: "loaded_instruments", label: "已載入標的" },
  { key: "configured_instruments", label: "Preset 標的" },
  { key: "watchlists", label: "觀察清單" },
  { key: "sample_symbols", label: "範例代號" },
];

const categoryColumns = [
  { key: "label", label: "分類" },
  { key: "instrument_count", label: "標的數" },
];

const availablePresets = computed(() => coverage.value?.data.preset.available_presets ?? [selectedPreset.value]);

const presetMetrics = computed(() => {
  const preset = coverage.value?.data.preset;
  if (!preset) {
    return [];
  }
  return [
    { label: "Preset 名稱", value: preset.preset_name, hint: "目前查詢對象" },
    { label: "宣告標的", value: formatNumber(preset.configured_instrument_count), hint: "config 內定義" },
    { label: "宣告清單", value: formatNumber(preset.configured_watchlist_count), hint: "preset watchlists" },
    { label: "Coverage 區段", value: formatNumber(preset.scopes_declared), hint: "scope definitions" },
  ];
});

const marketChartPoints = computed(() =>
  (coverage.value?.data.market_counts ?? []).map((item) => ({
    label: item.label,
    value: item.instrument_count,
    tone: "info" as const,
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
    market: scope.market,
    asset_type: scope.asset_type,
    loaded_instruments: scope.loaded_instrument_count,
    configured_instruments: scope.configured_instrument_count,
    watchlists: `${scope.loaded_watchlist_count}/${scope.configured_watchlist_count}`,
    sample_symbols: formatList(scope.sample_symbols, "無"),
  })),
);

const marketRows = computed(() =>
  (coverage.value?.data.market_counts ?? []).map((item) => ({
    label: item.label,
    instrument_count: item.instrument_count,
  })),
);

const sourceRouteRows = computed(() =>
  (coverage.value?.data.source_route_counts ?? []).map((item) => ({
    label: item.label,
    instrument_count: item.instrument_count,
  })),
);

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
