import { describe, expect, it } from "vitest";

import projectConfigSource from "../../project.config.json?raw";
import manifestSource from "../../src/manifest.json?raw";

function extractAppIds(source: string) {
  return Array.from(source.matchAll(/"appid"\s*:\s*"([^"]+)"/g)).map(
    (match) => match[1],
  );
}

describe("mini program configuration", () => {
  it("builds the 1.1.1 Mini Program release metadata", () => {
    expect(manifestSource).toContain('"versionName" : "1.1.1"');
    expect(manifestSource).toContain('"versionCode" : "111"');
  });

  it("builds with the authorized WeChat app id instead of touristappid", () => {
    const appIds = [...extractAppIds(manifestSource), ...extractAppIds(projectConfigSource)];

    expect(appIds.length).toBeGreaterThanOrEqual(3);
    for (const appId of appIds) {
      expect(appId).toMatch(/^wx[0-9a-f]{16}$/i);
      expect(appId).not.toBe("wx0000000000000000");
      expect(appId).not.toBe("touristappid");
    }
  });

  it("keeps dependency-analysis filtering disabled for generated component modules", () => {
    expect(manifestSource).toContain('"ignoreDevUnusedFiles" : false');
    expect(manifestSource).toContain('"ignoreUploadUnusedFiles" : false');
  });

  it("declares required private location APIs used by realtime map location", () => {
    expect(manifestSource).toContain('"requiredPrivateInfos"');
    expect(manifestSource).toContain('"getLocation"');
    expect(manifestSource).toContain('"startLocationUpdate"');
    expect(manifestSource).toContain('"onLocationChange"');
  });
});
