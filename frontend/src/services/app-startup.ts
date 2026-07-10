import type { CurrentUser } from "@/types/user";
import { LOGIN_ROUTE } from "@/services/auth-session";
import { ApiBusinessError } from "@/services/request";
import { requestWechatLoginCode } from "@/services/wechat-auth";

export { LOGIN_ROUTE };
export const HOME_ROUTE = "/pages/index/index";
export const CHANGE_PASSWORD_ROUTE = "/pages/auth/change-password";
export const PROFILE_SETUP_ROUTE = "/pages/profile/complete";

export type StartupRoute =
  | typeof LOGIN_ROUTE
  | typeof CHANGE_PASSWORD_ROUTE
  | typeof PROFILE_SETUP_ROUTE
  | typeof HOME_ROUTE;

export interface StartupUserSession {
  accessToken: string;
  loginWithWechat: (code: string) => Promise<unknown>;
  refreshCurrentUser: () => Promise<CurrentUser | null>;
  clearSession: () => void;
}

export type StartupResourceLoader = (
  currentUser: CurrentUser,
) => Promise<void> | void;

export type WechatLoginCodeProvider = () => Promise<string | null>;

const WECHAT_SESSION_REJECTED_CODES = new Set([40104, 40303, 40304, 40903]);

function shouldClearSessionAfterWechatLogin(error: unknown): boolean {
  return (
    error instanceof ApiBusinessError &&
    WECHAT_SESSION_REJECTED_CODES.has(error.code)
  );
}

async function loadMapResources(): Promise<void> {
  // Placeholder for map point data initialization.
}

async function loadTaskResources(): Promise<void> {
  // Placeholder for task data initialization.
}

async function loadRoleResources(_currentUser: CurrentUser): Promise<void> {
  // Placeholder for role-aware resources such as admin entry permissions.
}

export async function initializeAppResources(
  currentUser: CurrentUser,
): Promise<void> {
  await Promise.all([
    loadMapResources(),
    loadTaskResources(),
    loadRoleResources(currentUser),
  ]);
}

export async function resolveStartupRoute(
  session: StartupUserSession,
  initializeResources: StartupResourceLoader = initializeAppResources,
  getWechatLoginCode: WechatLoginCodeProvider = requestWechatLoginCode,
): Promise<StartupRoute> {
  const wechatCode = await getWechatLoginCode();
  if (wechatCode) {
    try {
      await session.loginWithWechat(wechatCode);
    } catch (error) {
      if (shouldClearSessionAfterWechatLogin(error)) {
        session.clearSession();
        return LOGIN_ROUTE;
      }

      if (!session.accessToken) {
        return LOGIN_ROUTE;
      }
    }
  }

  if (!session.accessToken) {
    return LOGIN_ROUTE;
  }

  try {
    const currentUser = await session.refreshCurrentUser();
    if (!currentUser) {
      session.clearSession();
      return LOGIN_ROUTE;
    }

    if (currentUser.must_change_password) {
      return CHANGE_PASSWORD_ROUTE;
    }

    if (!currentUser.profile_completed) {
      return PROFILE_SETUP_ROUTE;
    }

    await initializeResources(currentUser);
    return HOME_ROUTE;
  } catch {
    session.clearSession();
    return LOGIN_ROUTE;
  }
}
