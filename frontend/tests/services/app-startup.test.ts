import { describe, expect, it, vi } from "vitest";

import {
  HOME_ROUTE,
  LOGIN_ROUTE,
  resolveStartupRoute,
  type StartupUserSession,
} from "@/services/app-startup";
import type { CurrentUser } from "@/types/user";

const currentUser: CurrentUser = {
  id: "u1",
  student_no: "20252160A1010",
  role: "member",
  status: "active",
  nickname: "小林",
  avatar_url: null,
  must_change_password: false,
};

function createSession(
  accessToken: string,
  refreshCurrentUser = vi.fn<() => Promise<CurrentUser | null>>(),
): StartupUserSession {
  return {
    accessToken,
    refreshCurrentUser,
    clearSession: vi.fn(),
  };
}

describe("app startup flow", () => {
  it("routes to login when there is no access token", async () => {
    const session = createSession("");
    const initializeResources = vi.fn();

    await expect(
      resolveStartupRoute(session, initializeResources),
    ).resolves.toBe(LOGIN_ROUTE);
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
      resolveStartupRoute(session, initializeResources),
    ).resolves.toBe(HOME_ROUTE);
    expect(session.refreshCurrentUser).toHaveBeenCalledTimes(1);
    expect(initializeResources).toHaveBeenCalledWith(currentUser);
  });

  it("clears stale session and routes to login when user refresh fails", async () => {
    const session = createSession(
      "expired-token",
      vi.fn().mockRejectedValue(new Error("token expired")),
    );
    const initializeResources = vi.fn();

    await expect(
      resolveStartupRoute(session, initializeResources),
    ).resolves.toBe(LOGIN_ROUTE);
    expect(session.clearSession).toHaveBeenCalledTimes(1);
    expect(initializeResources).not.toHaveBeenCalled();
  });
});
