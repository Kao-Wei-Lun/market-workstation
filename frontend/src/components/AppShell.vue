<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed: !appStore.sidebarOpen }">
      <div class="brand">
        <strong>MW</strong>
        <span v-if="appStore.sidebarOpen">Market Workstation</span>
      </div>
      <nav class="nav-list">
        <RouterLink
          v-for="route in navRoutes"
          :key="route.name"
          :to="route.path"
          class="nav-link"
          active-class="active"
        >
          {{ route.meta?.label }}
        </RouterLink>
      </nav>
    </aside>
    <div class="content-shell">
      <header class="topbar">
        <button class="toggle" @click="appStore.toggleSidebar">
          {{ appStore.sidebarOpen ? "Hide" : "Show" }}
        </button>
        <div class="topbar-meta">
          <strong>{{ appStore.appTitle }}</strong>
          <span class="muted">API {{ appStore.apiBaseUrl }}</span>
        </div>
      </header>
      <main class="page">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";

import { routes } from "@/router/routes";
import { useAppStore } from "@/stores/app";

const appStore = useAppStore();
const navRoutes = routes;
</script>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 260px 1fr;
  min-height: 100vh;
}

.sidebar {
  padding: 1.2rem;
  border-right: 1px solid var(--border);
  background: linear-gradient(180deg, #10263f 0%, #173555 100%);
  color: #f4f8fb;
}

.sidebar.collapsed {
  width: 80px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.brand strong {
  display: inline-grid;
  width: 40px;
  height: 40px;
  place-items: center;
  background: rgba(255, 255, 255, 0.14);
  border-radius: 12px;
}

.nav-list {
  display: grid;
  gap: 0.35rem;
}

.nav-link {
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
  color: rgba(255, 255, 255, 0.78);
}

.nav-link.active,
.nav-link:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.content-shell {
  display: grid;
  grid-template-rows: auto 1fr;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(18px);
  background: rgba(255, 255, 255, 0.72);
  position: sticky;
  top: 0;
  z-index: 10;
}

.toggle {
  border: 1px solid var(--border);
  background: var(--panel-bg);
  border-radius: 12px;
  padding: 0.55rem 0.8rem;
  cursor: pointer;
}

.topbar-meta {
  display: grid;
  justify-items: end;
}

.page {
  padding: 1.5rem;
}

@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }
}
</style>
