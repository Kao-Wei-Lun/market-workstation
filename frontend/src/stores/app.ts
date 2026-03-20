import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { getApiBaseUrl } from "@/api/http";

export const useAppStore = defineStore("app", () => {
  const sidebarOpen = ref(true);
  const apiBaseUrl = ref(getApiBaseUrl());

  const appTitle = computed(() => "市場工作站");

  function toggleSidebar(): void {
    sidebarOpen.value = !sidebarOpen.value;
  }

  return {
    apiBaseUrl,
    appTitle,
    sidebarOpen,
    toggleSidebar,
  };
});
