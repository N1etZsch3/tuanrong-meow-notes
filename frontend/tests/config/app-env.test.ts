import { describe, expect, it } from "vitest";

import { appEnv, normalizeApiBaseUrl } from "@/config/app-env";

describe("app env config", () => {
  it("normalizes api base url without trailing slash", () => {
    expect(normalizeApiBaseUrl("http://localhost:8000/api/v1/")).toBe(
      "http://localhost:8000/api/v1",
    );
  });

  it("uses /api/v1 as the default api prefix", () => {
    expect(appEnv.apiBaseUrl.endsWith("/api/v1")).toBe(true);
  });
});
