import { beforeEach, describe, expect, it, vi } from "vitest";

import loginPageSource from "../../src/pages/login/index.vue?raw";

describe("login agreement memory", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("remembers agreement acceptance by account identifier", async () => {
    const saved: Record<string, unknown> = {};
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn((key: string) => saved[key]),
      setStorageSync: vi.fn((key: string, value: unknown) => {
        saved[key] = value;
      }),
    });

    const {
      hasAcceptedAgreementForAccount,
      rememberAgreementAcceptedForAccounts,
    } = await import("@/pages/login/agreement");

    expect(hasAcceptedAgreementForAccount("trmx0001")).toBe(false);

    rememberAgreementAcceptedForAccounts([" TRMX0001 ", "20252160A1010"]);

    expect(hasAcceptedAgreementForAccount("trmx0001")).toBe(true);
    expect(hasAcceptedAgreementForAccount("20252160a1010")).toBe(true);
    expect(hasAcceptedAgreementForAccount("trmx0002")).toBe(false);
  });

  it("uses remembered agreement state in the login page", () => {
    expect(loginPageSource).toContain("applyRememberedAgreement");
    expect(loginPageSource).toContain("hasAcceptedAgreementForAccount");
    expect(loginPageSource).toContain("rememberAgreementAcceptedForAccounts");
    expect(loginPageSource).toContain("watch(");
  });
});
