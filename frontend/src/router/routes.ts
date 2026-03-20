import type { RouteRecordRaw } from "vue-router";

import BacktestsPage from "@/pages/BacktestsPage.vue";
import CandidatesPage from "@/pages/CandidatesPage.vue";
import DerivativesPage from "@/pages/DerivativesPage.vue";
import GroupsPage from "@/pages/GroupsPage.vue";
import OverviewPage from "@/pages/OverviewPage.vue";
import ReportsPage from "@/pages/ReportsPage.vue";
import WatchlistsPage from "@/pages/WatchlistsPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/", name: "overview", component: OverviewPage, meta: { label: "Overview" } },
  { path: "/watchlists", name: "watchlists", component: WatchlistsPage, meta: { label: "Watchlists" } },
  { path: "/groups", name: "groups", component: GroupsPage, meta: { label: "Groups" } },
  { path: "/candidates", name: "candidates", component: CandidatesPage, meta: { label: "Candidates" } },
  { path: "/reports", name: "reports", component: ReportsPage, meta: { label: "Reports" } },
  { path: "/backtests", name: "backtests", component: BacktestsPage, meta: { label: "Backtests" } },
  { path: "/derivatives", name: "derivatives", component: DerivativesPage, meta: { label: "Derivatives" } },
];
