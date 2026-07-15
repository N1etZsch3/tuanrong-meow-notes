import { afterEach, describe, expect, it, vi } from "vitest";

import { MOCK_NOTIFICATIONS } from "@/pages/messages/mock-notifications";
import type { StoredLocalState } from "@/pages/messages/messages-page";
import {
  MESSAGES_UNREAD_INDICATOR_EVENT,
  publishMessagesUnreadIndicator,
  readMessagesUnreadIndicator,
  resolveMessagesUnreadIndicator,
} from "@/services/message-unread-indicator";

function allReadStates(): StoredLocalState[] {
  return MOCK_NOTIFICATIONS.map((message) => ({
    id: message.id,
    is_read: true,
    read_at: "2026-07-15T13:30:00+08:00",
    is_pinned: false,
    is_muted: false,
    is_dismissed: false,
    label_key: null,
  }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("message unread indicator", () => {
  it("shows for initial mock unread messages and hides after all are read", () => {
    expect(resolveMessagesUnreadIndicator(null)).toBe(true);
    expect(resolveMessagesUnreadIndicator(allReadStates())).toBe(false);
  });

  it("restores the indicator when one message is marked unread", () => {
    const stored = allReadStates();
    stored[0] = { ...stored[0], is_read: false, read_at: null };

    expect(resolveMessagesUnreadIndicator(stored)).toBe(true);
  });

  it("reads persisted state and publishes changes to every tab bar instance", () => {
    const emit = vi.fn();
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn(() => allReadStates()),
      $emit: emit,
    });

    expect(readMessagesUnreadIndicator()).toBe(false);
    publishMessagesUnreadIndicator(true);

    expect(emit).toHaveBeenCalledWith(MESSAGES_UNREAD_INDICATOR_EVENT, true);
  });
});
