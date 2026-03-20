<template>
  <section class="panel">
    <div class="panel-header">
      <SectionHeader :title="title" :description="description">
        <span v-if="entryCount" class="pill">{{ entryCount }} 欄</span>
      </SectionHeader>
    </div>
    <div class="panel-body">
      <div v-if="entries.length" class="payload-grid">
        <div v-for="entry in entries" :key="entry.key" class="payload-card">
          <p class="payload-label">{{ formatLabel(entry.key) }}</p>

          <RouterLink
            v-if="entry.link"
            :to="entry.link.to"
            class="payload-link"
          >
            {{ entry.link.label }}
          </RouterLink>

          <div v-else-if="entry.kind === 'array'" class="payload-pills">
            <template v-for="(item, index) in entry.arrayItems" :key="`${entry.key}-${index}`">
              <RouterLink
                v-if="item.link"
                :to="item.link.to"
                class="pill payload-pill-link"
              >
                {{ item.label }}
              </RouterLink>
              <span v-else class="pill">{{ item.label }}</span>
            </template>
          </div>

          <div v-else-if="entry.kind === 'object'" class="payload-nested">
            <div
              v-for="nestedEntry in entry.objectEntries"
              :key="`${entry.key}-${nestedEntry.key}`"
              class="payload-nested-row"
            >
              <span class="muted">{{ formatLabel(nestedEntry.key) }}</span>
              <span>{{ nestedEntry.value }}</span>
            </div>
          </div>

          <p v-else class="payload-value">{{ entry.value }}</p>
        </div>
      </div>
      <p v-else class="muted">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import type { RouteLocationRaw } from "vue-router";

import SectionHeader from "@/components/SectionHeader.vue";
import { formatTitle } from "@/utils/formatters";

interface PayloadLink {
  label: string;
  to: RouteLocationRaw;
}

interface ObjectEntry {
  key: string;
  value: string;
}

interface ArrayItem {
  label: string;
  link: PayloadLink | null;
}

interface DisplayEntry {
  key: string;
  kind: "value" | "array" | "object";
  value: string;
  link: PayloadLink | null;
  arrayItems: ArrayItem[];
  objectEntries: ObjectEntry[];
}

const props = withDefaults(
  defineProps<{
    title: string;
    payload: Record<string, unknown>;
    description?: string;
    emptyMessage?: string;
    resolveLink?: (key: string, value: unknown) => PayloadLink | null;
  }>(),
  {
    description: undefined,
    emptyMessage: "目前沒有可顯示的結構化內容。",
    resolveLink: undefined,
  },
);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isRenderable(value: unknown): boolean {
  if (value === null || value === undefined || value === "") {
    return false;
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  if (isRecord(value)) {
    return Object.keys(value).length > 0;
  }
  return true;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "無資料";
  }
  if (Array.isArray(value)) {
    return value.map((item) => renderValue(item)).join("、");
  }
  if (isRecord(value)) {
    return JSON.stringify(value);
  }
  return String(value);
}

function formatLabel(value: string): string {
  return formatTitle(value);
}

const entries = computed<DisplayEntry[]>(() =>
  Object.entries(props.payload)
    .filter(([, value]) => isRenderable(value))
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return {
          key,
          kind: "array" as const,
          value: "",
          link: null,
          arrayItems: value.map((item) => ({
            label: renderValue(item),
            link: props.resolveLink ? props.resolveLink(key, item) : null,
          })),
          objectEntries: [],
        };
      }
      if (isRecord(value)) {
        return {
          key,
          kind: "object" as const,
          value: "",
          link: null,
          arrayItems: [],
          objectEntries: Object.entries(value)
            .filter(([, nestedValue]) => isRenderable(nestedValue))
            .map(([nestedKey, nestedValue]) => ({
              key: nestedKey,
              value: renderValue(nestedValue),
            })),
        };
      }
      return {
        key,
        kind: "value" as const,
        value: renderValue(value),
        link: props.resolveLink ? props.resolveLink(key, value) : null,
        arrayItems: [],
        objectEntries: [],
      };
    }),
);

const entryCount = computed(() => entries.value.length);
</script>

<style scoped>
.payload-grid {
  display: grid;
  gap: 0.9rem;
}

.payload-card {
  display: grid;
  gap: 0.45rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.6);
}

.payload-label,
.payload-value {
  margin: 0;
}

.payload-label {
  font-size: 0.8rem;
  color: var(--muted);
}

.payload-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.payload-link,
.payload-pill-link {
  color: var(--accent);
  text-decoration: none;
}

.payload-link:hover,
.payload-pill-link:hover {
  text-decoration: underline;
}

.payload-nested {
  display: grid;
  gap: 0.4rem;
}

.payload-nested-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}
</style>
