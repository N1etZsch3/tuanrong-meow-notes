import { describe, expect, it, vi } from "vitest";

import {
  CHANGE_PASSWORD_ROUTE,
  HOME_ROUTE,
  LOGIN_ROUTE,
  PROFILE_SETUP_ROUTE,
  PUBLIC_HOME_ROUTE,
  resolveStartupRoute,
  type StartupUserSession,
} from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import type { CurrentUser } from "@/types/user";

const currentUser: CurrentUser = {
  id: "u1",
  student_no: "20252160A1010",
  role: "member",
  status: "active",
  nickname: "小林",
  avatar_url: null,
  must_change_password: false,
  profile_completed: true,
};

function createSession(
  accessToken: string,
  refreshCurrentUser = vi.fn<() => Promise<CurrentUser | null>>(),
): StartupUserSession & {
  loginWithWechat: ReturnType<
    typeof vi.fn<(code: string) => Promise<unknown>>
  >;
} {
  return {
    accessToken,
    refreshCurrentUser,
    clearSession: vi.fn(),
    loginWithWechat: vi.fn<(code: string) => Promise<unknown>>(),
  };
}

describe("app startup flow", () => {
  it("routes a guest with no access token to the public home", async () => {
    const session = createSession("");
    const initializeResources = vi.fn();
    const requestWechatCode = vi.fn().mockResolvedValue(null);

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(PUBLIC_HOME_ROUTE);
    expect(requestWechatCode).toHaveBeenCalledTimes(1);
    expect(session.loginWithWechat).not.toHaveBeenCalled();
    expect(session.refreshCurrentUser).not.toHaveBeenCalled();
    expect(initializeResources).not.toHaveBeenCalled();
  });

  it("logs in with WeChat before resolving the authenticated route", async () => {
    const refreshCurrentUser = vi.fn().mockResolvedValue(currentUser);
    const session = createSession("", refreshCurrentUser);
    session.loginWithWechat.mockImplementation(async () => {
      session.accessToken = "wechat-token";
    });
    const initializeResources = vi.fn().mockResolvedValue(undefined);
    const requestWechatCode = vi.fn().mockResolvedValue("wechat-code-1");

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(HOME_ROUTE);
    expect(requestWechatCode).toHaveBeenCalledTimes(1);
    expect(session.loginWithWechat).toHaveBeenCalledWith("wechat-code-1");
    expect(refreshCurrentUser).toHaveBeenCalledTimes(1);
    expect(initializeResources).toHaveBeenCalledWith(currentUser);
  });

  it("routes an unbound WeChat identity to the public home and clears any stale session", async () => {
    const session = createSession("stale-token");
    session.loginWithWechat.mockRejectedValue(
      new ApiBusinessError(40104, "微信账号尚未绑定喵喵号", "trace-unbound", null),
    );
    const initializeResources = vi.fn();
    const requestWechatCode = vi.fn().mockResolvedValue("unbound-code");

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(PUBLIC_HOME_ROUTE);
    expect(session.clearSession).toHaveBeenCalledTimes(1);
    expect(session.refreshCurrentUser).not.toHaveBeenCalled();
    expect(initializeResources).not.toHaveBeenCalled();
  });

  it("routes a disabled/mismatched member to the login page", async () => {
    const session = createSession("stale-token");
    session.loginWithWechat.mockRejectedValue(
      new ApiBusinessError(40304, "微信与喵喵号绑定不一致", "trace-mismatch", null),
    );
    const initializeResources = vi.fn();
    const requestWechatCode = vi.fn().mockResolvedValue("mismatch-code");

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(LOGIN_ROUTE);
    expect(session.clearSession).toHaveBeenCalledTimes(1);
    expect(session.refreshCurrentUser).not.toHaveBeenCalled();
  });

  it("keeps a valid local session when WeChat auto-login has a transient failure", async () => {
    const refreshCurrentUser = vi.fn().mockResolvedValue(currentUser);
    const session = createSession("local-token", refreshCurrentUser);
    session.loginWithWechat.mockRejectedValue(new Error("network unavailable"));
    const initializeResources = vi.fn().mockResolvedValue(undefined);
    const requestWechatCode = vi.fn().mockResolvedValue("wechat-code-1");

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(HOME_ROUTE);
    expect(session.clearSession).not.toHaveBeenCalled();
    expect(refreshCurrentUser).toHaveBeenCalledTimes(1);
    expect(initializeResources).toHaveBeenCalledWith(currentUser);
  });

  it("routes a guest to the public home when auto-login fails with no local session", async () => {
    const session = createSession("");
    session.loginWithWechat.mockRejectedValue(new Error("network unavailable"));
    const initializeResources = vi.fn();
    const requestWechatCode = vi.fn().mockResolvedValue("wechat-code-1");

    await expect(
      resolveStartupRoute(session, initializeResources, requestWechatCode),
    ).resolves.toBe(PUBLIC_HOME_ROUTE);
    expect(session.refreshCurrentUser).not.toHaveBeenCalled();
    expect(initializeResources).not.toHaveBeenCalled();
  });

  it("refreshes user and initializes resources before routing home", async () => {
    const session = createSession(
      "token-1",
      vi.fn().mockResolvedValue(currentUser),
    );
    const initializeResources = vi.fn().mockResolvedValue(undefined);

    await expect(
      resolveStartupRoute(
        session,
        initializeResources,
        vi.fn().mockResolvedValue(null),
      ),
    ).resolves.toBe(HOME_ROUTE);
    expect(session.refreshCurrentUser).toHaveBeenCalledTimes(1);
    expect(initializeResources).toHaveBeenCalledWith(currentUser);
  });

  it("routes to change password when the current user must update the initial password", async () => {
    const mustChangeUser: CurrentUser = {
      ...currentUser,
      must_change_password: true,
      profile_completed: false,
    };
    const session = createSession(
      "token-1",
      vi.fn().mockResolvedValue(mustChangeUser),
    );
    const initializeResources = vi.fn();

    await expect(
      resolveStartupRoute(
        session,
        initializeResources,
        vi.fn().mockResolvedValue(null),
      ),
    ).resolves.toBe(CHANGE_PASSWORD_ROUTE);
    expect(initializeResources).not.toHaveBeenCalled();
  });

  it("routes to profile setup when identity initialization is incomplete", async () => {
    const incompleteProfileUser: CurrentUser = {
      ...currentUser,
      must_change_password: false,
      profile_completed: false,
    };
    const session = createSession(
      "token-1",
      vi.fn().mockResolvedValue(incompleteProfileUser),
    );
    const initializeResources = vi.fn();

    await expect(
      resolveStartupRoute(
        session,
        initializeResources,
        vi.fn().mockResolvedValue(null),
      ),
    ).resolves.toBe(PROFILE_SETUP_ROUTE);
    expect(initializeResources).not.toHaveBeenCalled();
  });

  it("clears stale session and routes to login when user refresh fails", async () => {
    const session = createSession(
      "expired-token",
      vi.fn().mockRejectedValue(new Error("token expired")),
    );
    const initializeResources = vi.fn();

    await expect(
      resolveStartupRoute(
        session,
        initializeResources,
        vi.fn().mockResolvedValue(null),
      ),
    ).resolves.toBe(LOGIN_ROUTE);
    expect(session.clearSession).toHaveBeenCalledTimes(1);
    expect(initializeResources).not.toHaveBeenCalled();
  });
});
