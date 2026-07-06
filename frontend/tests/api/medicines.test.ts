import { describe, expect, it, vi } from "vitest";

import {
  approveMedicineApplication,
  createMedicine,
  createMedicineApplication,
  getMedicineApplicationDetail,
  getMedicineApplications,
  getMedicineCategories,
  getMedicineHoldingLogs,
  getMedicines,
  getMedicineLogs,
  recordMedicineAdjustment,
  recordMedicinePurchase,
} from "@/api/medicines";

function mockSuccess(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-medicines",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("medicines api", () => {
  it("requests categories and medicine list filters", async () => {
    const requestMock = mockSuccess({ items: [], page: 1, page_size: 20, total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await getMedicineCategories("token-1");
    await getMedicines("token-1", {
      category_id: "category-1",
      holding_relation: "mine",
      keyword: "",
      page: 1,
    });

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicine-categories"),
        header: expect.objectContaining({ Authorization: "Bearer token-1" }),
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicines"),
        data: {
          category_id: "category-1",
          holding_relation: "mine",
          page: 1,
        },
      }),
    );
  });

  it("creates a new medicine catalog and holding", async () => {
    const requestMock = mockSuccess({ medicine_id: "medicine-1", holding_id: "holding-1" });
    vi.stubGlobal("uni", { request: requestMock });

    await createMedicine("token-1", {
      catalog: {
        name: "阿莫西林",
        category_id: "category-1",
        specification: "250mg/片",
        unit: "片",
      },
      initial_quantity: 20,
      remark: "第一次建档",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/medicines"),
        data: expect.objectContaining({
          initial_quantity: 20,
          catalog: expect.objectContaining({ name: "阿莫西林" }),
        }),
      }),
    );
  });

  it("records purchase and application approval actions", async () => {
    const requestMock = mockSuccess({ current_quantity: 30 });
    vi.stubGlobal("uni", { request: requestMock });

    await recordMedicinePurchase("token-1", "holding-1", {
      quantity: 10,
      source: "线下购买",
      remark: "补充库存",
    });
    await createMedicineApplication("token-2", "holding-1", {
      quantity: 3,
      reason_text: "北门小黑后续用药",
    });
    await approveMedicineApplication("token-1", "application-1", {
      review_comment: "已线下分配",
    });

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/medicine-holdings/holding-1/purchase"),
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/medicine-holdings/holding-1/applications"),
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/medicine-applications/application-1/approve"),
      }),
    );
  });

  it("requests medicine logs, holding logs, adjustments and application lists", async () => {
    const requestMock = mockSuccess({ items: [], page: 1, page_size: 20, total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await getMedicineLogs("token-1", "medicine-1", { page: 2 });
    await getMedicineHoldingLogs("token-1", "holding-1", { page_size: 10 });
    await recordMedicineAdjustment("token-1", "holding-1", {
      quantity: 18,
      reason_text: "线下盘点校正",
    });
    await getMedicineApplications("token-1", { scope: "review", status: "pending" });
    await getMedicineApplicationDetail("token-1", "application-1");

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicines/medicine-1/logs"),
        data: { page: 2 },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicine-holdings/holding-1/logs"),
        data: { page_size: 10 },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/medicine-holdings/holding-1/adjust"),
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      4,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicine-applications"),
        data: { scope: "review", status: "pending" },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      5,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/medicine-applications/application-1"),
      }),
    );
  });
});
