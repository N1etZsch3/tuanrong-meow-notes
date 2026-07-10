import { afterEach, describe, expect, it, vi } from "vitest";

import { requestWechatLoginCode } from "@/services/wechat-auth";

describe("WeChat auth service", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requests a Mini Program login code from the WeChat provider", async () => {
    const login = vi.fn((options: UniNamespace.LoginOptions) => {
      options.success?.({
        code: "wechat-code-1",
        errMsg: "login:ok",
        authResult: "",
      });
    });
    vi.stubGlobal("uni", { login });

    await expect(requestWechatLoginCode()).resolves.toBe("wechat-code-1");
    expect(login).toHaveBeenCalledWith(
      expect.objectContaining({ provider: "weixin" }),
    );
  });

  it("returns null when Mini Program login is unavailable", async () => {
    vi.stubGlobal("uni", {});

    await expect(requestWechatLoginCode()).resolves.toBeNull();
  });

  it("returns null when Mini Program login fails", async () => {
    const login = vi.fn((options: UniNamespace.LoginOptions) => {
      options.fail?.({ errMsg: "login:fail" });
    });
    vi.stubGlobal("uni", { login });

    await expect(requestWechatLoginCode()).resolves.toBeNull();
  });
});
