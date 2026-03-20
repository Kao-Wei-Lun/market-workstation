import type { RouteRecordRaw } from "vue-router";

import BacktestsPage from "@/pages/BacktestsPage.vue";
import CandidatesPage from "@/pages/CandidatesPage.vue";
import DerivativesPage from "@/pages/DerivativesPage.vue";
import GroupsPage from "@/pages/GroupsPage.vue";
import OverviewPage from "@/pages/OverviewPage.vue";
import ReportsPage from "@/pages/ReportsPage.vue";
import WatchlistsPage from "@/pages/WatchlistsPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/", name: "overview", component: OverviewPage, meta: { label: "Overview", title: "Market Overview", description: "Daily market snapshot and cross-page entry point." } },
  { path: "/watchlists", name: "watchlists", component: WatchlistsPage, meta: { label: "Watchlists", title: "Watchlists", description: "Review watchlist membership, scanner flags, and summary metrics." } },
  { path: "/groups", name: "groups", component: GroupsPage, meta: { label: "Tag Groups", title: "Tag Groups", description: "Inspect tag-based groups and scanner context." } },
  { path: "/candidates", name: "candidates", component: CandidatesPage, meta: { label: "Candidates", title: "Next-Day Candidates", description: "Ranked next-day candidate runs with reasons and score breakdowns." } },
  { path: "/reports", name: "reports", component: ReportsPage, meta: { label: "Reports", title: "Daily Reports", description: "Bundle sections and persisted daily report rows." } },
  { path: "/backtests", name: "backtests", component: BacktestsPage, meta: { label: "Backtests", title: "Backtests", description: "Recent research runs, metrics, and trade-level results." } },
  { path: "/derivatives", name: "derivatives", component: DerivativesPage, meta: { label: "Derivatives", title: "Taiwan Derivatives", description: "Institutional futures/options bias and anomaly summaries." } },
];
