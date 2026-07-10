import { beforeEach, describe, expect, it, vi } from "vitest";

import loadingPageSource from "../../src/pages/loading/index.vue?raw";
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

  it("uses a login confirmation modal instead of a WeChat binding checkbox", () => {
    expect(loginPageSource).toContain(
      "登录后，当前微信将自动与该喵喵号绑定，用于后续自动登录和账号保护。如需更换微信，请联系管理员解绑。",
    );
    expect(loginPageSource).toContain("confirmWechatBindingLogin");
    expect(loginPageSource).toContain("uni.showModal");
    expect(loginPageSource).not.toContain('class="binding-consent"');
    expect(loginPageSource).not.toContain("wechat_bind_agreed");
    expect(loginPageSource).not.toContain("onWechatBindAgreementChange");
  });

  it("confirms binding before requesting a code and submitting password login", () => {
    const bindingPrompt = loginPageSource.indexOf(
      "await confirmWechatBindingLogin()",
    );
    const requestCode = loginPageSource.indexOf("await requestWechatLoginCode()");
    const passwordLogin = loginPageSource.indexOf("userStore.loginWithPassword");

    expect(bindingPrompt).toBeGreaterThan(-1);
    expect(requestCode).toBeGreaterThan(bindingPrompt);
    expect(passwordLogin).toBeGreaterThan(requestCode);
    expect(loginPageSource).toContain('confirmText: "确认登录"');
    expect(loginPageSource).toContain('cancelText: "取消"');
  });

  it("requires a WeChat code and sends explicit binding consent after confirmation", () => {
    expect(loginPageSource).toContain("requestWechatLoginCode");
    expect(loginPageSource).toContain("暂时无法获取微信登录凭证，请重试");
    expect(loginPageSource).toContain("wechat_code: wechatCode");
    expect(loginPageSource).toContain("agree_wechat_bind: true");
    expect(loginPageSource).not.toContain("wechat_code: wechatCode || undefined");
  });

  it("keeps startup WeChat auto-login silent", () => {
    expect(loadingPageSource).toContain("resolveStartupRoute(userStore)");
    expect(loadingPageSource).not.toContain("uni.showModal");
    expect(loadingPageSource).not.toContain("uni.showToast");
    expect(loadingPageSource).not.toContain("微信绑定");
  });
});
