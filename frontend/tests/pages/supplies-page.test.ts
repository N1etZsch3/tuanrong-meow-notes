import { describe, expect, it } from "vitest";

import adminSupplyCreateSource from "../../src/pages/admin/supplies/create.vue?raw";
import adminSupplyLocationSource from "../../src/pages/admin/supplies/location.vue?raw";
import supplyDetailSource from "../../src/pages/supplies/detail.vue?raw";
import supplyIndexSource from "../../src/pages/supplies/index.vue?raw";
import suppliesApiSource from "../../src/api/supplies.ts?raw";
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

describe("supply point detail page", () => {
  it("registers and renders a searchable supply point list page", () => {
    expect(pagesJson).toContain("pages/supplies/index");
    expect(supplyIndexSource).toContain("getMapPoints");
    expect(supplyIndexSource).toContain("filterPointListByKeyword");
    expect(supplyIndexSource).toContain('point_types: "supply"');
    expect(supplyIndexSource).toContain('placeholder="搜索物资点 / 附近地标"');
    expect(supplyIndexSource).toContain('class="point-card"');
    expect(supplyIndexSource).toContain("nearby_landmark_name");
    expect(supplyIndexSource).toContain("/pages/supplies/detail?supply_point_id=");
    expect(supplyIndexSource).toContain('class="back-button"');
    expect(supplyIndexSource).toContain("function goBack");
    expect(supplyIndexSource).toContain("uni.navigateBack()");
    expect(supplyIndexSource).toContain('v-if="userStore.isAdmin"');
    expect(supplyIndexSource).toContain('class="floating-add admin-floating-add"');
    expect(supplyIndexSource).toContain("新增物资点");
    expect(supplyIndexSource).toContain("goCreateSupplyPoint");
    expect(supplyIndexSource).toContain("/pages/admin/supplies/create");
    expect(supplyIndexSource).not.toContain("<AppTabBar");
    expect(supplyIndexSource).not.toContain('class="filter-card"');
  });

  it("searches nearby public POIs independently from the supply point name", () => {
    const nearbySource = extractFunctionSource(adminSupplyLocationSource, "loadNearbyPoiCandidates");

    expect(nearbySource).toContain("keyword: getLocationPickerPoiKeyword()");
    expect(nearbySource).not.toContain("keyword: selectedLocation.location_name");
  });

  it("uses one-shot location handoff storage instead of keeping supply drafts", () => {
    const pickerReadSource = extractFunctionSource(adminSupplyLocationSource, "readLocationTransfer");
    const formReadSource = extractFunctionSource(adminSupplyCreateSource, "readSelectedLocation");

    expect(pickerReadSource).toContain("uni.removeStorageSync(SUPPLY_LOCATION_STORAGE_KEY)");
    expect(formReadSource).toContain("uni.removeStorageSync(SUPPLY_LOCATION_STORAGE_KEY)");
  });

  it("returns to the supply list after deleting a supply point", () => {
    const deleteSource = extractFunctionSource(adminSupplyCreateSource, "deleteCurrentSupplyPoint");

    expect(deleteSource).toContain('returnToListAfterDelete("/pages/supplies/index")');
    expect(deleteSource).not.toContain('uni.switchTab({ url: "/pages/index/index" })');
  });

  it("returns to and refreshes the existing supply detail after saving an edit", () => {
    const submitSource = extractFunctionSource(adminSupplyCreateSource, "submitSupplyPoint");

    expect(submitSource).toContain("completeCreateOrEditNavigation");
    expect(submitSource).toContain("isEditMode: isEditMode.value");
    expect(submitSource).not.toContain("uni.redirectTo");
    expect(supplyDetailSource).toContain('import { onLoad, onShow } from "@dcloudio/uni-app"');
    expect(supplyDetailSource).toMatch(/onShow\(\(\) => \{\s*void loadSupplyDetail/);
  });

  it("starts and resets supply point selection at the current user location", () => {
    const resetSource = extractFunctionSource(adminSupplyLocationSource, "resetLocation");

    expect(adminSupplyLocationSource).toContain("getCachedUserLocation");
    expect(adminSupplyLocationSource).toContain("refreshUserLocation");
    expect(adminSupplyLocationSource).toContain("void placeAtCurrentUserLocation()");
    expect(adminSupplyLocationSource).toContain(':show-location="true"');
    expect(resetSource).toContain("void placeAtCurrentUserLocation({ silent: false })");
    expect(resetSource).not.toContain("HBNU_DEFAULT_SUPPLY_LOCATION");
  });

  it("lets admins drag supply point photos to change the cover order", () => {
    expect(adminSupplyCreateSource).toContain("SortableImageGrid");
    expect(adminSupplyCreateSource).toContain('@reorder="reorderPhoto"');
    expect(adminSupplyCreateSource).toContain("moveArrayItem(form.photos");
  });

  it("opens supply point photos with the native image preview", () => {
    expect(supplyDetailSource).toContain("uni.previewImage({");
    expect(supplyDetailSource).toContain("urls: resolvedUrls");
    expect(supplyDetailSource).not.toContain("ImagePreviewModal");
    expect(supplyDetailSource).not.toContain("imagePreviewVisible");
  });

  it("lets members adjust selected supply quantities before submitting a record", () => {
    const payloadSource = extractFunctionSource(supplyDetailSource, "recordPayloadItems");

    expect(supplyDetailSource).toContain("recordItemQuantities");
    expect(supplyDetailSource).toContain('class="record-quantity-stepper"');
    expect(supplyDetailSource).toContain("changeRecordItemQuantity");
    expect(payloadSource).toContain("recordItemQuantities.value[itemId]");
  });

  it("shows the saved supply record remark in the record detail modal", () => {
    expect(supplyDetailSource).toContain("viewingRecord.remark");
    expect(supplyDetailSource).toContain('class="modal-record-remark"');
  });

  it("refreshes only dynamic supply records when changing the record filter", () => {
    const filterSource = extractFunctionSource(supplyDetailSource, "changeRecordFilter");

    expect(suppliesApiSource).toContain("getSupplyRecords");
    expect(supplyDetailSource).toContain("loadSupplyRecordsOnly");
    expect(filterSource).toContain("loadSupplyRecordsOnly");
    expect(filterSource).not.toContain("loadSupplyDetail");
  });
});
