import { describe, expect, it } from "vitest";

import manifestSource from "../../src/manifest.json?raw";

describe("mini program configuration", () => {
  it("builds with the authorized WeChat app id instead of touristappid", () => {
    expect(manifestSource).toContain('"appid" : "wx0000000000000000"');
    expect(manifestSource).not.toContain('"appid" : ""');
    expect(manifestSource).not.toContain("touristappid");
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
