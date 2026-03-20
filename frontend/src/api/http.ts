import axios, { AxiosError, type AxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const browserOrigin =
  typeof window !== "undefined" && window.location?.origin ? window.location.origin : "this frontend origin";

export const http = axios.create({
  baseURL,
  timeout: 10000,
});

export class ApiClientError extends Error {
  kind: "network" | "http" | "unknown";
  status: number | null;
  detail: string;

  constructor(message: string, options?: { kind?: "network" | "http" | "unknown"; status?: number | null; detail?: string }) {
    super(message);
    this.name = "ApiClientError";
    this.kind = options?.kind ?? "unknown";
    this.status = options?.status ?? null;
    this.detail = options?.detail ?? message;
  }
}

function extractErrorDetail(payload: unknown): string | null {
  if (typeof payload === "string") {
    return payload;
  }
  if (!payload || typeof payload !== "object") {
    return null;
  }
  if ("detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === "string" ? item : JSON.stringify(item)))
        .join("; ");
    }
  }
  return null;
}

export function normalizeApiError(error: unknown): ApiClientError {
  if (error instanceof ApiClientError) {
    return error;
  }
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    if (!axiosError.response) {
      const detail =
        `Unable to reach API at ${baseURL}. This is usually a network or CORS problem. ` +
        `If the backend is running, ensure it allows requests from ${browserOrigin}.`;
      return new ApiClientError(detail, {
        kind: "network",
        detail,
      });
    }
    const status = axiosError.response.status ?? null;
    const detail =
      extractErrorDetail(axiosError.response.data) ??
      `API request failed with status ${status ?? "unknown"}.`;
    return new ApiClientError(detail, {
      kind: "http",
      status,
      detail,
    });
  }
  if (error instanceof Error) {
    return new ApiClientError(error.message, { kind: "unknown" });
  }
  return new ApiClientError("Unknown API error", { kind: "unknown" });
}

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(normalizeApiError(error)),
);

export async function getJson<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.get<T>(url, config);
  return response.data;
}

export async function postJson<TResponse, TRequest = unknown>(
  url: string,
  data?: TRequest,
  config?: AxiosRequestConfig,
): Promise<TResponse> {
  const response = await http.post<TResponse>(url, data, config);
  return response.data;
}

export function getApiBaseUrl(): string {
  return baseURL;
}
