import { describe, expect, it } from "vitest";

import adminLandmarkCreateSource from "../../src/pages/admin/landmarks/create.vue?raw";
import landmarkDetailSource from "../../src/pages/landmarks/detail.vue?raw";
import landmarkIndexSource from "../../src/pages/landmarks/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";

function extractFunctionSource(source: string, functionName: string): string {
  const normalStart = source.indexOf(`function ${functionName}`);
  const asyncStart = source.indexOf(`async function ${functionName}`);
  const start = normalStart >= 0 ? normalStart : asyncStart;
  expect(start).toBeGreaterThanOrEqual(0);
  const bodyStart = source.indexOf("{", start);
  expect(bodyStart).toBeGreaterThan(start);

  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(start, index + 1);
      }
    }
  }

  return source.slice(start);
}

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
    expect(landmarkIndexSource).toContain('class="back-button"');
    expect(landmarkIndexSource).toContain("function goBack");
    expect(landmarkIndexSource).toContain("uni.navigateBack()");
    expect(landmarkIndexSource).toContain('v-if="userStore.isAdmin"');
    expect(landmarkIndexSource).toContain('class="floating-add admin-floating-add"');
    expect(landmarkIndexSource).toContain("新增地标");
    expect(landmarkIndexSource).toContain("goCreateLandmark");
    expect(landmarkIndexSource).toContain("/pages/admin/landmarks/create");
    expect(landmarkIndexSource).not.toContain("<AppTabBar");
    expect(landmarkIndexSource).not.toContain('class="filter-card"');
  });

  it("returns to the landmark list after deleting a landmark", () => {
    const deleteSource = extractFunctionSource(adminLandmarkCreateSource, "deleteCurrentLandmark");

    expect(deleteSource).toContain('returnToListAfterDelete("/pages/landmarks/index")');
    expect(deleteSource).not.toContain('uni.switchTab({ url: "/pages/index/index" })');
  });

  it("returns to and refreshes the existing landmark detail after saving an edit", () => {
    const submitSource = extractFunctionSource(adminLandmarkCreateSource, "submitLandmark");

    expect(submitSource).toContain("completeCreateOrEditNavigation");
    expect(submitSource).toContain("isEditMode: isEditMode.value");
    expect(submitSource).not.toContain("uni.redirectTo");
    expect(landmarkDetailSource).toContain('import { onLoad, onShow } from "@dcloudio/uni-app"');
    expect(landmarkDetailSource).toMatch(/onShow\(\(\) => \{\s*void loadLandmarkDetail/);
  });
});
