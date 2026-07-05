import { describe, expect, it } from "vitest";

import landmarkIndexSource from "../../src/pages/landmarks/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";

describe("landmark list page", () => {
  it("registers and renders a searchable campus landmark list page", () => {
    expect(pagesJson).toContain("pages/landmarks/index");
    expect(pagesJson).toContain("pages/landmarks/detail");
    expect(landmarkIndexSource).toContain("getMapPoints");
    expect(landmarkIndexSource).toContain("filterPointListByKeyword");
    expect(landmarkIndexSource).toContain('point_types: "landmark"');
    expect(landmarkIndexSource).toContain('placeholder="搜索校园地标 / 附近位置"');
    expect(landmarkIndexSource).toContain('class="point-card"');
    expect(landmarkIndexSource).toContain("nearby_landmark_name");
    expect(landmarkIndexSource).toContain("/pages/landmarks/detail?landmark_id=");
    expect(landmarkIndexSource).not.toContain('class="filter-card"');
  });
});
