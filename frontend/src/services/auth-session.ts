import { STORAGE_KEYS } from "@/constants/storage";

export const LOGIN_ROUTE = "/pages/login/index";

type AuthExpiredHandler = () => void;

let authExpiredHandler: AuthExpiredHandler | null = null;
let isRedirectingToLogin = false;

export function isAuthExpiredCode(code: number): boolean {
  return code === 40101 || code === 40102;
}

export function setAuthExpiredHandler(handler: AuthExpiredHandler | null) {
  authExpiredHandler = handler;
}

export function clearStoredSession() {
  uni.removeStorageSync(STORAGE_KEYS.accessToken);
  uni.removeStorageSync(STORAGE_KEYS.currentUser);
}

export function redirectToLogin() {
  if (isRedirectingToLogin) {
    return;
  }

  isRedirectingToLogin = true;
  uni.reLaunch({
    url: LOGIN_ROUTE,
    complete: () => {
      isRedirectingToLogin = false;
    },
  });
}

export function handleAuthExpired() {
  if (authExpiredHandler) {
    authExpiredHandler();
    return;
  }

  clearStoredSession();
  redirectToLogin();
}
