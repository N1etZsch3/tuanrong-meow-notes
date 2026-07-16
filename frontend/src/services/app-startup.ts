import type { CurrentUser } from "@/types/user";
import { LOGIN_ROUTE } from "@/services/auth-session";
import { ApiBusinessError } from "@/services/request";
import { requestWechatLoginCode } from "@/services/wechat-auth";

export { LOGIN_ROUTE };
export const HOME_ROUTE = "/pages/index/index";
export const PUBLIC_HOME_ROUTE = "/pages/public/home";
export const CHANGE_PASSWORD_ROUTE = "/pages/auth/change-password";
export const PROFILE_SETUP_ROUTE = "/pages/profile/complete";

export type StartupRoute =
  | typeof LOGIN_ROUTE
  | typeof PUBLIC_HOME_ROUTE
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

// An unbound WeChat identity means the visitor is a guest -> show the public zone.
const WECHAT_UNBOUND_CODE = 40104;
// Anomalous member states (disabled / mismatched / already bound) are not guests;
// route them to the member login page and its "contact admin" guidance.
const WECHAT_SESSION_REJECTED_CODES = new Set([40303, 40304, 40903]);

function wechatErrorCode(error: unknown): number | null {
  return error instanceof ApiBusinessError ? error.code : null;
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
      const code = wechatErrorCode(error);

      // Unbound WeChat: a guest (or a member whose binding was cleared). Drop any
      // stale local session and show the public zone; the member entry there leads
      // back to login for first-bind / re-bind.
      if (code === WECHAT_UNBOUND_CODE) {
        session.clearSession();
        return PUBLIC_HOME_ROUTE;
      }

      // Disabled / mismatched / already-bound accounts are members with a problem;
      // send them to the login page instead of the guest zone.
      if (code !== null && WECHAT_SESSION_REJECTED_CODES.has(code)) {
        session.clearSession();
        return LOGIN_ROUTE;
      }

      // Transient failure (network, WeChat service). Keep a still-valid local
      // session and fall through; a guest with no session lands on public home.
      if (!session.accessToken) {
        return PUBLIC_HOME_ROUTE;
      }
    }
  }

  if (!session.accessToken) {
    return PUBLIC_HOME_ROUTE;
  }

  try {
    const currentUser = await session.refreshCurrentUser();
    if (!currentUser) {
      // A token was present but could not be refreshed: this was a member
      // session, so recover through the login page rather than the guest zone.
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
