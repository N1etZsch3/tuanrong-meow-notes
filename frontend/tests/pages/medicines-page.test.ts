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
  applySelectedMedicineToDraft,
  buildMedicineCreatePayload,
  clearSelectedMedicineDraft,
  createDefaultMedicineDraft,
  formatMedicineQuantity,
  getMedicineCategoryClass,
  getMedicineLogToneClass,
  getMedicineOperationLabel,
  getMedicineStockTone,
  isMedicineLogVisibleForFilter,
  isMedicineCatalogLinked,
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
    expect(medicineIndexSource).toContain(">药品</text>");
    expect(medicineIndexSource).not.toContain(">药品管理</text>");
    expect(medicineIndexSource).toContain('class="back-button"');
    expect(medicineIndexSource).toContain("function goBack");
    expect(medicineIndexSource).toContain('class="search-box"');
    expect(medicineIndexSource).toContain('class="filter-card"');
    expect(medicineIndexSource).toContain("holding_relation");
    expect(medicineIndexSource).toContain('class="floating-add"');
    expect(medicineIndexSource).toContain("goCreateMedicine");
    expect(medicineIndexSource).toContain("/pages/medicines/create");
    expect(medicineIndexSource).toContain("/pages/medicines/detail?medicine_id=");
    expect(medicineIndexSource).toContain("素材/svg/喵记/药品.svg");
    expect(medicineIndexSource).toContain("getMedicineCategoryClass");
    expect(medicineIndexSource).toContain('class="category-tag"');
    expect(medicineIndexSource).toContain('class="holder-inventory-card"');
    expect(medicineIndexSource).not.toContain('class="medicine-stats"');
    expect(medicineIndexSource).not.toContain("holder_count }} 位持有人");
    expect(medicineIndexSource).not.toContain("medicine.specification");
    expect(medicineIndexSource).not.toContain("total_current_quantity");
    expect(medicineIndexSource).not.toContain("AppTabBar");
  });

  it("creates medicines with inline catalog suggestions and image upload", () => {
    expect(medicineCreateSource).toContain("createMedicine");
    expect(medicineCreateSource).toContain("listAdminUsers");
    expect(medicineCreateSource).toContain("searchMedicines");
    expect(medicineCreateSource).not.toContain("modeOptions");
    expect(medicineCreateSource).toContain("validateMedicineCreateDraft");
    expect(medicineCreateSource).toContain("buildMedicineCreatePayload");
    expect(medicineCreateSource).not.toContain("建档方式");
    expect(medicineCreateSource).not.toContain("创建新药品");
    expect(medicineCreateSource).not.toContain("选择已有药品");
    expect(medicineCreateSource).toContain('@input="handleMedicineNameInput"');
    expect(medicineCreateSource).toContain('class="catalog-suggestion-list"');
    expect(medicineCreateSource).toContain('class="selected-medicine-tag"');
    expect(medicineCreateSource).toContain("clearSelectedMedicine");
    expect(medicineCreateSource).toContain("MEDICINE_IMAGE_LIMIT");
    expect(medicineCreateSource).toContain("remainingImageSlots");
    expect(medicineCreateSource).toContain("category_name");
    expect(medicineCreateSource).toContain("其他（默认）");
    expect(medicineCreateSource).toContain("自定义分类");
    expect(medicineCreateSource).toContain("count: remainingImageSlots.value");
    expect(medicineCreateSource).toContain('usage_type: "medicine_photo"');
    expect(medicineCreateSource).not.toContain('usage_type: "medicine_cover"');
    expect(medicineCreateSource).toContain('v-for="photo in draft.photo_urls"');
    expect(medicineCreateSource).toContain("canAssignHolder");
    expect(medicineCreateSource).toContain("holderKeyword");
    expect(medicineCreateSource).toContain('class="holder-suggestion-list"');
    expect(medicineCreateSource).toContain("selectHolder");
    expect(medicineCreateSource).toContain("clearSelectedHolder");
    expect(medicineCreateSource).toContain("请从列表中选择持有人");
    expect(medicineCreateSource).toContain("chooseMedicineImage");
    expect(medicineCreateSource).toContain("uploadImage");
    expect(medicineCreateSource).toContain("cover_image_url");
    expect(medicineCreateSource).toContain(':disabled="isCatalogLinked"');
    expect(medicineCreateSource).toContain("初始数量");
    expect(medicineCreateSource).toContain("/pages/medicines/detail?medicine_id=");
  });

  it("shows medicine detail with holder cards and stock dynamics", () => {
    expect(medicineDetailSource).toContain("getMedicineDetail");
    expect(medicineDetailSource).toContain("updateMedicineCatalog");
    expect(medicineDetailSource).toContain("goHoldingDetail");
    expect(medicineDetailSource).toContain("/pages/medicines/holding?holding_id=");
    expect(medicineDetailSource).toContain("recent_logs");
    expect(medicineDetailSource).toContain("can_edit_catalog");
    expect(medicineDetailSource).toContain("openEditCatalogModal");
    expect(medicineDetailSource).toContain('class="holder-inventory-card"');
    expect(medicineDetailSource).toContain('class="medicine-info-panel"');
    expect(medicineDetailSource).toContain("药品说明");
    expect(medicineDetailSource).toContain("logFilterOptions");
    expect(medicineDetailSource).toContain("filteredRecentLogs");
    expect(medicineDetailSource).toContain("openLogModal");
    expect(medicineDetailSource).toContain("药品动态详情");
    expect(medicineDetailSource).toContain("getMedicineLogToneClass");
    expect(medicineDetailSource).not.toContain("累计入库");
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

  it("builds validated create payloads for manually entered and linked medicines", () => {
    expect(validateMedicineCreateDraft(createDefaultMedicineDraft())).toEqual({
      valid: false,
      message: "请输入药品名称",
    });

    const newDraft = createDefaultMedicineDraft();
    newDraft.name = " 阿莫西林 ";
    newDraft.category_id = "category-1";
    newDraft.specification = "250mg/片";
    newDraft.unit = "片";
    newDraft.cover_image_url = "https://img.example.com/amoxicillin.jpg";
    newDraft.photo_urls = [
      "https://img.example.com/amoxicillin.jpg",
      "https://img.example.com/amoxicillin-box.jpg",
    ];
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
        cover_image_url: "https://img.example.com/amoxicillin.jpg",
        photo_urls: [
          "https://img.example.com/amoxicillin.jpg",
          "https://img.example.com/amoxicillin-box.jpg",
        ],
      },
      initial_quantity: 12,
      remark: "第一次建档",
    });

    const sameNameDraft = createDefaultMedicineDraft();
    sameNameDraft.name = "阿莫西林";
    sameNameDraft.unit = "片";
    sameNameDraft.initial_quantity = 1;

    expect(buildMedicineCreatePayload(sameNameDraft)).toEqual({
      catalog: {
        name: "阿莫西林",
        category_name: "其他",
        specification: null,
        unit: "片",
        description: null,
        usage_notes: null,
        cover_image_url: null,
        photo_urls: [],
      },
      initial_quantity: 1,
      remark: null,
    });

    const assignedDraft = createDefaultMedicineDraft();
    assignedDraft.holder_id = "holder-1";
    assignedDraft.name = "生理盐水";
    assignedDraft.unit = "瓶";
    assignedDraft.initial_quantity = 2;

    expect(buildMedicineCreatePayload(assignedDraft)).toEqual({
      holder_id: "holder-1",
      catalog: {
        name: "生理盐水",
        category_name: "其他",
        specification: null,
        unit: "瓶",
        description: null,
        usage_notes: null,
        cover_image_url: null,
        photo_urls: [],
      },
      initial_quantity: 2,
      remark: null,
    });

    const customCategoryDraft = createDefaultMedicineDraft();
    customCategoryDraft.name = "皮肤喷剂";
    customCategoryDraft.category_name = "皮肤护理";
    customCategoryDraft.unit = "瓶";
    customCategoryDraft.initial_quantity = 2;

    expect(buildMedicineCreatePayload(customCategoryDraft)).toEqual({
      catalog: {
        name: "皮肤喷剂",
        category_name: "皮肤护理",
        specification: null,
        unit: "瓶",
        description: null,
        usage_notes: null,
        cover_image_url: null,
        photo_urls: [],
      },
      initial_quantity: 2,
      remark: null,
    });

    const linkedDraft = applySelectedMedicineToDraft(
      {
        ...createDefaultMedicineDraft(),
        initial_quantity: 3,
      },
      {
        medicine_id: "medicine-1",
        name: "阿莫西林",
        category: { id: "category-1", name: "抗生素" },
        specification: "250mg/片",
        unit: "片",
        description: "常用抗生素",
        usage_notes: "遵医嘱使用",
        cover_image_url: "https://img.example.com/amoxicillin.jpg",
      },
    );

    expect(isMedicineCatalogLinked(linkedDraft)).toBe(true);
    expect(validateMedicineCreateDraft(linkedDraft)).toEqual({ valid: true });
    expect(buildMedicineCreatePayload(linkedDraft)).toEqual({
      medicine_id: "medicine-1",
      initial_quantity: 3,
      remark: null,
    });

    const clearedDraft = clearSelectedMedicineDraft(linkedDraft);
    expect(isMedicineCatalogLinked(clearedDraft)).toBe(false);
    expect(clearedDraft).toMatchObject({
      selected_medicine_id: "",
      name: "",
      category_id: "",
      specification: "",
      unit: "",
      description: "",
      usage_notes: "",
      cover_image_url: "",
      photo_urls: [],
      initial_quantity: 3,
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
    expect(getMedicineCategoryClass("抗生素")).toBe("category-antibiotic");
    expect(getMedicineCategoryClass("未知分类")).toBe("category-other");
    expect(getMedicineLogToneClass("purchase")).toBe("log-purchase");
    expect(getMedicineLogToneClass("use_self")).toBe("log-use");
    expect(getMedicineLogToneClass("scrap")).toBe("log-other");
    expect(isMedicineLogVisibleForFilter("use_self", "use")).toBe(true);
    expect(isMedicineLogVisibleForFilter("purchase", "use")).toBe(false);
    expect(isMedicineLogVisibleForFilter("initial_in", "purchase")).toBe(true);
  });
});
