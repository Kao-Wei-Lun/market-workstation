import type { RouteRecordRaw } from "vue-router";

import BacktestsPage from "@/pages/BacktestsPage.vue";
import CandidatesPage from "@/pages/CandidatesPage.vue";
import CoveragePage from "@/pages/CoveragePage.vue";
import DerivativesPage from "@/pages/DerivativesPage.vue";
import GroupsPage from "@/pages/GroupsPage.vue";
import OperationsPage from "@/pages/OperationsPage.vue";
import OverviewPage from "@/pages/OverviewPage.vue";
import ReportsPage from "@/pages/ReportsPage.vue";
import WatchlistsPage from "@/pages/WatchlistsPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/", name: "overview", component: OverviewPage, meta: { label: "總覽", title: "市場總覽", description: "每日市場快照與跨頁面檢視入口。" } },
  { path: "/coverage", name: "coverage", component: CoveragePage, meta: { label: "資料覆蓋", title: "資料覆蓋", description: "檢查資料範圍預設集、已載入標的與初始化狀態。" } },
  { path: "/operations", name: "operations", component: OperationsPage, meta: { label: "系統狀態", title: "系統狀態", description: "檢查資料新鮮度、匯入工作與 worker 健康狀態。" } },
  { path: "/watchlists", name: "watchlists", component: WatchlistsPage, meta: { label: "觀察清單", title: "觀察清單", description: "檢視觀察清單成員、掃描訊號與摘要指標。" } },
  { path: "/groups", name: "groups", component: GroupsPage, meta: { label: "標籤群組", title: "標籤群組", description: "檢視標籤群組、群組強弱與掃描脈絡。" } },
  { path: "/candidates", name: "candidates", component: CandidatesPage, meta: { label: "候選清單", title: "隔日候選清單", description: "檢視隔日候選名單、評分理由與排名拆解。" } },
  { path: "/reports", name: "reports", component: ReportsPage, meta: { label: "報表", title: "每日報表", description: "檢視日報彙整區塊與已保存的報表內容。" } },
  { path: "/backtests", name: "backtests", component: BacktestsPage, meta: { label: "回測", title: "回測研究", description: "檢視近期研究回測、核心指標與交易明細。" } },
  { path: "/derivatives", name: "derivatives", component: DerivativesPage, meta: { label: "衍生性商品", title: "台灣法人衍生性商品", description: "檢視台灣法人期權偏多偏空與異常摘要。" } },
];
