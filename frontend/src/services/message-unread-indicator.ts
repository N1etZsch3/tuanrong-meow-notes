import {
  MESSAGES_LOCAL_STATE_STORAGE_KEY,
  countUnread,
  indexLocalStates,
  toNotificationView,
  type StoredLocalState,
} from "@/pages/messages/messages-page";
import { MOCK_NOTIFICATIONS } from "@/pages/messages/mock-notifications";

export const MESSAGES_UNREAD_INDICATOR_EVENT = "cat-map:messages-unread-change";

export function resolveMessagesUnreadIndicator(
  storedStates: StoredLocalState[] | null | undefined,
): boolean {
  const storedIndex = indexLocalStates(storedStates);
  const messages = MOCK_NOTIFICATIONS.map((dto) =>
    toNotificationView(dto, storedIndex[dto.id]),
  );
  return countUnread(messages) > 0;
}

export function readMessagesUnreadIndicator(): boolean {
  try {
    const raw = uni.getStorageSync(MESSAGES_LOCAL_STATE_STORAGE_KEY) as
      | StoredLocalState[]
      | "";
    return resolveMessagesUnreadIndicator(Array.isArray(raw) ? raw : null);
  } catch {
    return resolveMessagesUnreadIndicator(null);
  }
}

export function publishMessagesUnreadIndicator(hasUnread: boolean): void {
  uni.$emit(MESSAGES_UNREAD_INDICATOR_EVENT, hasUnread);
}
