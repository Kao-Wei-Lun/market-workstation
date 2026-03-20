import { defineStore } from "pinia";
import { ref } from "vue";

import { fetchWatchlists } from "@/api/watchlists";
import type { WatchlistRead } from "@/types/dashboard";

export const useWatchlistsStore = defineStore("watchlists", () => {
  const items = ref<WatchlistRead[]>([]);
  const isLoading = ref(false);
  const hasLoaded = ref(false);

  async function load(): Promise<void> {
    if (isLoading.value) {
      return;
    }
    isLoading.value = true;
    try {
      items.value = await fetchWatchlists();
      hasLoaded.value = true;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    hasLoaded,
    isLoading,
    items,
    load,
  };
});
