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

  it("lets the backend decide when agreement is required", () => {
    expect(loginPageSource).not.toContain("请先勾选协议");
  });

  it("clearly tells the user that WeChat will be bound to the meow account", () => {
    expect(loginPageSource).toContain(
      "登录后，当前微信将与该喵喵号绑定，用于后续自动登录和账号保护。如需更换微信，请联系管理员解绑。",
    );
    expect(loginPageSource).toContain("wechat_bind_agreed");
    expect(loginPageSource).toContain("onWechatBindAgreementChange");
  });

  it("blocks binding before password login until the user acknowledges it", () => {
    const consentCheck = loginPageSource.indexOf(
      "if (wechatCode && !form.wechat_bind_agreed)",
    );
    const passwordLogin = loginPageSource.indexOf("userStore.loginWithPassword");

    expect(consentCheck).toBeGreaterThan(-1);
    expect(passwordLogin).toBeGreaterThan(consentCheck);
    expect(loginPageSource).toContain("请确认微信与喵喵号绑定");
  });

  it("only sends binding consent when a WeChat login code is available", () => {
    expect(loginPageSource).toContain("requestWechatLoginCode");
    expect(loginPageSource).toContain("wechat_code: wechatCode || undefined");
    expect(loginPageSource).toContain(
      "agree_wechat_bind: Boolean(wechatCode && form.wechat_bind_agreed)",
    );
  });
});
