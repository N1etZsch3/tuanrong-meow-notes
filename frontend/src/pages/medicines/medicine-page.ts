import type { MedicineCreatePayload } from "@/api/medicines";

export type MedicineHoldingRelation = "all" | "mine" | "others";
export type MedicineCreateMode = "new" | "existing";
export type MedicineStockTone = "empty" | "low" | "normal";

export interface MedicineOption {
  label: string;
  value: string;
}

export interface MedicineCreateDraft {
  mode: MedicineCreateMode;
  selected_medicine_id: string;
  name: string;
  category_id: string;
  specification: string;
  unit: string;
  description: string;
  usage_notes: string;
  initial_quantity: number;
  remark: string;
}

export interface MedicineValidationResult {
  valid: boolean;
  message?: string;
}

export const MEDICINE_HOLDING_RELATION_OPTIONS: MedicineOption[] = [
  { label: "全部", value: "all" },
  { label: "我持有", value: "mine" },
  { label: "其他成员", value: "others" },
];

export const MEDICINE_SORT_OPTIONS: MedicineOption[] = [
  { label: "最近更新", value: "recent" },
  { label: "库存最多", value: "stock" },
  { label: "名称", value: "name" },
];

export const MEDICINE_STOCK_STATUS_OPTIONS: MedicineOption[] = [
  { label: "全部", value: "" },
  { label: "库存正常", value: "normal" },
  { label: "库存较少", value: "low" },
  { label: "暂无库存", value: "empty" },
];

const MEDICINE_OPERATION_LABELS: Record<string, string> = {
  initial_in: "初始入库",
  purchase: "购入",
  use_self: "使用",
  scrap: "报废",
  distribute_out: "分配转出",
  distribute_in: "分配转入",
  transfer_out: "转交转出",
  transfer_in: "转交转入",
  application_use: "申请使用",
  adjustment: "库存校正",
  archive: "归档",
  delete_holding: "删除库存",
};

function nullableTrim(value: string): string | null {
  const normalized = value.trim();
  return normalized || null;
}

export function createDefaultMedicineDraft(): MedicineCreateDraft {
  return {
    mode: "new",
    selected_medicine_id: "",
    name: "",
    category_id: "",
    specification: "",
    unit: "",
    description: "",
    usage_notes: "",
    initial_quantity: 0,
    remark: "",
  };
}

export function validateMedicineCreateDraft(
  draft: MedicineCreateDraft,
): MedicineValidationResult {
  if (draft.mode === "existing" && !draft.selected_medicine_id) {
    return { valid: false, message: "请选择已有药品" };
  }

  if (draft.mode === "new" && !draft.name.trim()) {
    return { valid: false, message: "请输入药品名称" };
  }

  if (draft.mode === "new" && !draft.unit.trim()) {
    return { valid: false, message: "请输入计量单位" };
  }

  if (!Number.isFinite(draft.initial_quantity) || draft.initial_quantity <= 0) {
    return { valid: false, message: "请输入初始数量" };
  }

  return { valid: true };
}

export function buildMedicineCreatePayload(
  draft: MedicineCreateDraft,
): MedicineCreatePayload {
  const basePayload = {
    initial_quantity: Number(draft.initial_quantity),
    remark: nullableTrim(draft.remark),
  };

  if (draft.mode === "existing") {
    return {
      ...basePayload,
      medicine_id: draft.selected_medicine_id,
    };
  }

  return {
    ...basePayload,
    catalog: {
      name: draft.name.trim(),
      category_id: nullableTrim(draft.category_id),
      specification: nullableTrim(draft.specification),
      unit: draft.unit.trim(),
      description: nullableTrim(draft.description),
      usage_notes: nullableTrim(draft.usage_notes),
      cover_image_url: null,
    },
  };
}

export function formatMedicineQuantity(quantity: number, unit: string): string {
  return `${Number(quantity).toLocaleString("zh-CN", {
    maximumFractionDigits: 2,
  })} ${unit}`;
}

export function getMedicineStockTone(status: string | null | undefined): MedicineStockTone {
  if (status === "empty" || status === "out_of_stock") {
    return "empty";
  }
  if (status === "low" || status === "warning") {
    return "low";
  }
  return "normal";
}

export function getMedicineStockClass(status: string | null | undefined): string {
  return `stock-${getMedicineStockTone(status)}`;
}

export function getMedicineOperationLabel(operationType: string): string {
  return MEDICINE_OPERATION_LABELS[operationType] || operationType;
}
