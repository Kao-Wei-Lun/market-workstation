import { createRouter, createWebHistory } from "vue-router";

import { routes } from "@/router/routes";

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.afterEach((to) => {
  const title = typeof to.meta.title === "string" ? to.meta.title : "Dashboard";
  document.title = `${title} | Market Workstation`;
});
