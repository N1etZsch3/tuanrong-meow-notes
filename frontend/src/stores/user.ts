import { defineStore } from "pinia";

import { STORAGE_KEYS } from "@/constants/storage";
import type { CurrentUser } from "@/types/user";

interface UserState {
  accessToken: string;
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

export const useUserStore = defineStore("user", {
  state: (): UserState => ({
    accessToken: readStorageString(STORAGE_KEYS.accessToken),
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
    setSession(accessToken: string, currentUser: CurrentUser) {
      this.accessToken = accessToken;
      this.currentUser = currentUser;
      uni.setStorageSync(STORAGE_KEYS.accessToken, accessToken);
      uni.setStorageSync(STORAGE_KEYS.currentUser, currentUser);
    },
    setCurrentUser(currentUser: CurrentUser) {
      this.currentUser = currentUser;
      uni.setStorageSync(STORAGE_KEYS.currentUser, currentUser);
    },
    clearSession() {
      this.accessToken = "";
      this.currentUser = null;
      uni.removeStorageSync(STORAGE_KEYS.accessToken);
      uni.removeStorageSync(STORAGE_KEYS.currentUser);
    },
  },
});
