import { describe, expect, it } from "vitest";

import {
  appEnv,
  normalizeApiBaseUrl,
  resolveApiBaseUrl,
} from "@/config/app-env";

describe("app env config", () => {
  it("normalizes api base url without trailing slash", () => {
    expect(normalizeApiBaseUrl("http://localhost:8000/api/v1/")).toBe(
      "http://localhost:8000/api/v1",
    );
  });

  it("uses /api/v1 as the current api prefix", () => {
    expect(appEnv.apiBaseUrl.endsWith("/api/v1")).toBe(true);
  });

  it("uses local api only for development when no explicit base url exists", () => {
    expect(resolveApiBaseUrl({ DEV: true })).toBe("http://localhost:8000/api/v1");
  });

  it("requires explicit api domain for production builds", () => {
    expect(() => resolveApiBaseUrl({ PROD: true })).toThrow(
      "VITE_API_BASE_URL",
    );
  });

  it("uses the configured api domain for production builds", () => {
    expect(
      resolveApiBaseUrl({
        PROD: true,
        VITE_API_BASE_URL: "https://api.example.com/api/v1/",
      }),
    ).toBe("https://api.example.com/api/v1");
  });

  it("rejects local api urls in production builds", () => {
    expect(() =>
      resolveApiBaseUrl({
        PROD: true,
        VITE_API_BASE_URL: "http://localhost:8000/api/v1",
      }),
    ).toThrow("生产构建不能使用本地 API 地址");
  });
});
