import { describe, expect, it } from "vitest";

import pagesJson from "../../src/pages.json?raw";
import meowNotesSource from "../../src/pages/tasks/index.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import medicineCreateSource from "../../src/pages/medicines/create.vue?raw";
import medicineDetailSource from "../../src/pages/medicines/detail.vue?raw";
import medicineHoldingSource from "../../src/pages/medicines/holding.vue?raw";
import medicineIndexSource from "../../src/pages/medicines/index.vue?raw";
import {
  MEDICINE_HOLDING_RELATION_OPTIONS,
  buildMedicineCreatePayload,
  createDefaultMedicineDraft,
  formatMedicineQuantity,
  getMedicineOperationLabel,
  getMedicineStockTone,
  validateMedicineCreateDraft,
} from "../../src/pages/medicines/medicine-page";

describe("medicine management pages", () => {
  it("registers medicine list, create, detail and holding pages", () => {
    expect(pagesJson).toContain("pages/medicines/index");
    expect(pagesJson).toContain("pages/medicines/create");
    expect(pagesJson).toContain("pages/medicines/detail");
    expect(pagesJson).toContain("pages/medicines/holding");
  });

  it("adds a Meow Notes bookshelf entry without changing bottom tabs or profile menu", () => {
    expect(meowNotesSource).toContain("药品");
    expect(meowNotesSource).toContain('/pages/medicines/index');
    expect(profileIndexSource).not.toContain("/pages/medicines/index");
    expect(profileIndexSource).not.toContain("goMedicines");
    expect(pagesJson).not.toMatch(/tabBar[\s\S]*pages\/medicines\/index/);
  });

  it("reuses the task list pattern and exposes create entry on medicine list", () => {
    expect(medicineIndexSource).toContain("getMedicines");
    expect(medicineIndexSource).toContain("getMedicineCategories");
    expect(medicineIndexSource).toContain('class="search-box"');
    expect(medicineIndexSource).toContain('class="filter-card"');
    expect(medicineIndexSource).toContain("holding_relation");
    expect(medicineIndexSource).toContain('class="add-medicine-button"');
    expect(medicineIndexSource).toContain("goCreateMedicine");
    expect(medicineIndexSource).toContain("/pages/medicines/create");
    expect(medicineIndexSource).toContain("/pages/medicines/detail?medicine_id=");
    expect(medicineIndexSource).not.toContain("AppTabBar");
  });

  it("creates medicines from either a new catalog or an existing catalog", () => {
    expect(medicineCreateSource).toContain("createMedicine");
    expect(medicineCreateSource).toContain("searchMedicines");
    expect(medicineCreateSource).toContain("modeOptions");
    expect(medicineCreateSource).toContain("validateMedicineCreateDraft");
    expect(medicineCreateSource).toContain("buildMedicineCreatePayload");
    expect(medicineCreateSource).toContain("创建新药品");
    expect(medicineCreateSource).toContain("选择已有药品");
    expect(medicineCreateSource).toContain("初始数量");
    expect(medicineCreateSource).toContain("/pages/medicines/detail?medicine_id=");
  });

  it("shows medicine detail with holder cards and stock dynamics", () => {
    expect(medicineDetailSource).toContain("getMedicineDetail");
    expect(medicineDetailSource).toContain("goHoldingDetail");
    expect(medicineDetailSource).toContain("/pages/medicines/holding?holding_id=");
    expect(medicineDetailSource).toContain("recent_logs");
    expect(medicineDetailSource).toContain('class="holder-card"');
    expect(medicineDetailSource).toContain('class="medicine-dynamic-card"');
  });

  it("lets holders record stock actions and lets non-holders apply", () => {
    expect(medicineHoldingSource).toContain("getMedicineHoldingDetail");
    expect(medicineHoldingSource).toContain("recordMedicinePurchase");
    expect(medicineHoldingSource).toContain("recordMedicineUse");
    expect(medicineHoldingSource).toContain("recordMedicineScrap");
    expect(medicineHoldingSource).toContain("createMedicineApplication");
    expect(medicineHoldingSource).toContain("approveMedicineApplication");
    expect(medicineHoldingSource).toContain("记录购入");
    expect(medicineHoldingSource).toContain("记录使用");
    expect(medicineHoldingSource).toContain("记录报废");
    expect(medicineHoldingSource).toContain("申请使用");
    expect(medicineHoldingSource).toContain("通过申请");
  });

  it("builds validated create payloads for new and existing medicines", () => {
    expect(validateMedicineCreateDraft(createDefaultMedicineDraft())).toEqual({
      valid: false,
      message: "请输入药品名称",
    });

    const newDraft = createDefaultMedicineDraft();
    newDraft.name = " 阿莫西林 ";
    newDraft.category_id = "category-1";
    newDraft.specification = "250mg/片";
    newDraft.unit = "片";
    newDraft.initial_quantity = 12;
    newDraft.remark = " 第一次建档 ";

    expect(validateMedicineCreateDraft(newDraft)).toEqual({ valid: true });
    expect(buildMedicineCreatePayload(newDraft)).toEqual({
      catalog: {
        name: "阿莫西林",
        category_id: "category-1",
        specification: "250mg/片",
        unit: "片",
        description: null,
        usage_notes: null,
        cover_image_url: null,
      },
      initial_quantity: 12,
      remark: "第一次建档",
    });

    const existingDraft = createDefaultMedicineDraft();
    existingDraft.mode = "existing";
    existingDraft.selected_medicine_id = "medicine-1";
    existingDraft.initial_quantity = 3;

    expect(buildMedicineCreatePayload(existingDraft)).toEqual({
      medicine_id: "medicine-1",
      initial_quantity: 3,
      remark: null,
    });
  });

  it("formats list labels and stock status consistently", () => {
    expect(MEDICINE_HOLDING_RELATION_OPTIONS.map((item) => item.label)).toEqual([
      "全部",
      "我持有",
      "其他成员",
    ]);
    expect(getMedicineStockTone("empty")).toBe("empty");
    expect(getMedicineStockTone("low")).toBe("low");
    expect(getMedicineStockTone("normal")).toBe("normal");
    expect(formatMedicineQuantity(2.5, "片")).toBe("2.5 片");
    expect(getMedicineOperationLabel("purchase")).toBe("购入");
    expect(getMedicineOperationLabel("application_use")).toBe("申请使用");
  });
});
