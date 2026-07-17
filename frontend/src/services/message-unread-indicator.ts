import type { StoredLocalState } from "@/pages/messages/messages-page";

export const MESSAGES_UNREAD_INDICATOR_EVENT = "cat-map:messages-unread-change";

/** 喵息未读红点的持久化标志（供 AppTabBar 挂载时读取初值）。 */
export const MESSAGES_UNREAD_FLAG_STORAGE_KEY = "cat_map_messages_unread_flag_v1";

export function readMessagesUnreadIndicator(): boolean {
  try {
    return Boolean(uni.getStorageSync(MESSAGES_UNREAD_FLAG_STORAGE_KEY));
  } catch {
    return false;
  }
}

export function publishMessagesUnreadIndicator(hasUnread: boolean): void {
  try {
    uni.setStorageSync(MESSAGES_UNREAD_FLAG_STORAGE_KEY, hasUnread);
  } catch {
    // 存储失败不影响事件广播。
  }
  uni.$emit(MESSAGES_UNREAD_INDICATOR_EVENT, hasUnread);
}

/** 兼容旧签名：从本地标记推断是否有未读（现由喵息页服务端数据驱动）。 */
export function resolveMessagesUnreadIndicator(
  storedStates: StoredLocalState[] | null | undefined,
): boolean {
  if (!storedStates) {
    return false;
  }
  return storedStates.some((state) => state.is_read === false && !state.is_dismissed);
}
