import { afterEach, describe, expect, it, vi } from "vitest";

import type { StoredLocalState } from "@/pages/messages/messages-page";
import {
  MESSAGES_UNREAD_FLAG_STORAGE_KEY,
  MESSAGES_UNREAD_INDICATOR_EVENT,
  publishMessagesUnreadIndicator,
  readMessagesUnreadIndicator,
  resolveMessagesUnreadIndicator,
} from "@/services/message-unread-indicator";

function makeState(overrides: Partial<StoredLocalState>): StoredLocalState {
  return {
    id: "ntf-1",
    is_read: true,
    read_at: "2026-07-15T13:30:00+08:00",
    is_pinned: false,
    is_muted: false,
    is_dismissed: false,
    label_key: null,
    ...overrides,
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("message unread indicator", () => {
  it("resolves unread from stored local states", () => {
    expect(resolveMessagesUnreadIndicator(null)).toBe(false);
    expect(resolveMessagesUnreadIndicator([makeState({ is_read: true })])).toBe(false);
    expect(
      resolveMessagesUnreadIndicator([makeState({ is_read: false })]),
    ).toBe(true);
    expect(
      resolveMessagesUnreadIndicator([
        makeState({ is_read: false, is_dismissed: true }),
      ]),
    ).toBe(false);
  });

  it("reads the persisted boolean flag", () => {
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn((key: string) =>
        key === MESSAGES_UNREAD_FLAG_STORAGE_KEY ? true : "",
      ),
      setStorageSync: vi.fn(),
      $emit: vi.fn(),
    });
    expect(readMessagesUnreadIndicator()).toBe(true);
  });

  it("persists the flag and publishes changes to every tab bar instance", () => {
    const emit = vi.fn();
    const setStorageSync = vi.fn();
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn(() => ""),
      setStorageSync,
      $emit: emit,
    });

    publishMessagesUnreadIndicator(true);

    expect(setStorageSync).toHaveBeenCalledWith(MESSAGES_UNREAD_FLAG_STORAGE_KEY, true);
    expect(emit).toHaveBeenCalledWith(MESSAGES_UNREAD_INDICATOR_EVENT, true);
  });
});
