import { describe, expect, it } from "vitest";

import supplyDetailSource from "../../src/pages/supplies/detail.vue?raw";
import suppliesApiSource from "../../src/api/supplies.ts?raw";

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
