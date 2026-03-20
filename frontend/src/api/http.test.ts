import axios, { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { ApiClientError, normalizeApiError } from "@/api/http";

describe("normalizeApiError", () => {
  it("passes through ApiClientError instances", () => {
    const error = new ApiClientError("failed", { status: 500, detail: "failed" });
    expect(normalizeApiError(error)).toBe(error);
  });

  it("extracts fastapi detail from axios responses", () => {
    const error = new AxiosError("Request failed", undefined, undefined, undefined, {
      data: { detail: "report not found" },
      status: 404,
      statusText: "Not Found",
      headers: {},
      config: { headers: axios.AxiosHeaders.from({}) },
    });
    const normalized = normalizeApiError(error);
    expect(normalized.detail).toBe("report not found");
    expect(normalized.status).toBe(404);
  });
});
