import { defineStore } from "pinia";

import {
  getCurrentUser,
  login,
  logout,
  normalizeCurrentUser,
  normalizeLoginUser,
  renewAccessToken,
  type LoginPayload,
} from "@/api/auth";
import { STORAGE_KEYS } from "@/constants/storage";
import type { CurrentUser } from "@/types/user";

const ACCESS_TOKEN_RENEW_THRESHOLD_MS = 24 * 60 * 60 * 1000;

interface UserState {
  accessToken: string;
  accessTokenExpiresAt: number | null;
  currentUser: CurrentUser | null;
}

function readStorageString(key: string): string {
  const value = uni.getStorageSync(key);
  return typeof value === "string" ? value : "";
}

function readStorageObject<T>(key: string): T | null {
  const value = uni.getStorageSync(key);
  return value && typeof value === "object" ? (value as T) : null;
}

function readStorageNumber(key: string): number | null {
  const value = uni.getStorageSync(key);
  return typeof value === "number" ? value : null;
}

function resolveExpiresAt(expiresInSeconds: number): number {
  return Date.now() + expiresInSeconds * 1000;
}

export const useUserStore = defineStore("user", {
  state: (): UserState => ({
    accessToken: readStorageString(STORAGE_KEYS.accessToken),
    accessTokenExpiresAt: readStorageNumber(STORAGE_KEYS.accessTokenExpiresAt),
    currentUser: readStorageObject<CurrentUser>(STORAGE_KEYS.currentUser),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.accessToken && state.currentUser),
    isAdmin: (state) =>
      state.currentUser?.role === "admin" ||
      state.currentUser?.role === "super_admin",
    mustChangePassword: (state) =>
      Boolean(state.currentUser?.must_change_password),
  },
  actions: {
    setAccessToken(accessToken: string, expiresInSeconds?: number) {
      this.accessToken = accessToken;
      uni.setStorageSync(STORAGE_KEYS.accessToken, accessToken);
      if (typeof expiresInSeconds === "number") {
        this.accessTokenExpiresAt = resolveExpiresAt(expiresInSeconds);
        uni.setStorageSync(STORAGE_KEYS.accessTokenExpiresAt, this.accessTokenExpiresAt);
      }
    },
    setSession(
      accessToken: string,
      currentUser: CurrentUser,
      expiresInSeconds?: number,
    ) {
      this.setAccessToken(accessToken, expiresInSeconds);
      this.currentUser = currentUser;
      uni.setStorageSync(STORAGE_KEYS.currentUser, currentUser);
    },
    setCurrentUser(currentUser: CurrentUser) {
      this.currentUser = currentUser;
      uni.setStorageSync(STORAGE_KEYS.currentUser, currentUser);
    },
    async loginWithPassword(payload: LoginPayload) {
      const response = await login(payload);
      this.setSession(
        response.access_token,
        normalizeLoginUser(response),
        response.expires_in,
      );
      return response;
    },
    shouldRenewAccessToken(now = Date.now()) {
      if (!this.accessTokenExpiresAt) {
        return false;
      }

      const remainingMs = this.accessTokenExpiresAt - now;
      return remainingMs > 0 && remainingMs <= ACCESS_TOKEN_RENEW_THRESHOLD_MS;
    },
    isAccessTokenExpired(now = Date.now()) {
      return Boolean(this.accessTokenExpiresAt && this.accessTokenExpiresAt <= now);
    },
    async ensureFreshAccessToken() {
      if (!this.accessToken) {
        return null;
      }

      if (this.isAccessTokenExpired()) {
        this.clearSession();
        return null;
      }

      if (this.shouldRenewAccessToken()) {
        const response = await renewAccessToken(this.accessToken);
        this.setAccessToken(response.access_token, response.expires_in);
      }

      return this.accessToken;
    },
    async refreshCurrentUser() {
      const accessToken = await this.ensureFreshAccessToken();
      if (!accessToken) {
        return null;
      }

      const response = await getCurrentUser(accessToken);
      const currentUser = normalizeCurrentUser(response);
      this.setCurrentUser(currentUser);
      return currentUser;
    },
    async logoutFromServer() {
      if (this.accessToken) {
        await logout(this.accessToken);
      }

      this.clearSession();
    },
    clearSession() {
      this.accessToken = "";
      this.accessTokenExpiresAt = null;
      this.currentUser = null;
      uni.removeStorageSync(STORAGE_KEYS.accessToken);
      uni.removeStorageSync(STORAGE_KEYS.accessTokenExpiresAt);
      uni.removeStorageSync(STORAGE_KEYS.currentUser);
    },
  },
});
