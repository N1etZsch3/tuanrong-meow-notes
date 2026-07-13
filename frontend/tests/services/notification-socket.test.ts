import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  buildNotificationSocketUrl,
  connectNotificationChannel,
  parseNotificationEnvelope,
  type NotificationSocketStatus,
} from "@/services/notification-socket";
import type { NotificationItemDto } from "@/pages/messages/messages-page";

function buildDto(overrides: Partial<NotificationItemDto> = {}): NotificationItemDto {
  return {
    id: "ntf-live-1",
    notification_type: "new_task",
    title: "新任务已发布",
    content: "测试内容",
    related_type: "task",
    related_id: "task-1",
    is_read: false,
    read_at: null,
    created_at: "2026-07-13T09:00:00+08:00",
    ...overrides,
  };
}

describe("notification socket url and envelope", () => {
  it("derives the websocket endpoint from the api base url", () => {
    expect(buildNotificationSocketUrl("https://trmx.example/api/v1")).toBe(
      "wss://trmx.example/api/v1/ws/notifications",
    );
    expect(buildNotificationSocketUrl("http://localhost:8000/api/v1/")).toBe(
      "ws://localhost:8000/api/v1/ws/notifications",
    );
  });

  it("parses only valid notification.new envelopes", () => {
    const dto = buildDto();
    expect(
      parseNotificationEnvelope(JSON.stringify({ type: "notification.new", data: dto })),
    ).toMatchObject({ id: "ntf-live-1", notification_type: "new_task" });

    expect(parseNotificationEnvelope(JSON.stringify({ type: "ping" }))).toBeNull();
    expect(parseNotificationEnvelope("not-json")).toBeNull();
    expect(
      parseNotificationEnvelope(JSON.stringify({ type: "notification.new", data: {} })),
    ).toBeNull();
    expect(parseNotificationEnvelope({ type: "notification.new", data: dto })).toMatchObject({
      id: "ntf-live-1",
    });
  });
});

describe("mock notification channel", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("connects then replays pushes in order", () => {
    const statuses: NotificationSocketStatus[] = [];
    const received: string[] = [];

    connectNotificationChannel(
      {
        mode: "mock",
        connect_delay_ms: 500,
        pushes: [
          { delay_ms: 1000, notification: buildDto({ id: "p1" }) },
          { delay_ms: 2000, notification: buildDto({ id: "p2" }) },
        ],
      },
      {
        onNotification: (item) => received.push(item.id),
        onStatusChange: (status) => statuses.push(status),
      },
    );

    expect(statuses).toEqual(["connecting"]);
    vi.advanceTimersByTime(500);
    expect(statuses).toEqual(["connecting", "connected"]);
    vi.advanceTimersByTime(1000);
    expect(received).toEqual(["p1"]);
    vi.advanceTimersByTime(1000);
    expect(received).toEqual(["p1", "p2"]);
  });

  it("stops pushing and reports closed after close", () => {
    const statuses: NotificationSocketStatus[] = [];
    const received: string[] = [];

    const handle = connectNotificationChannel(
      {
        mode: "mock",
        connect_delay_ms: 100,
        pushes: [{ delay_ms: 1000, notification: buildDto({ id: "p1" }) }],
      },
      {
        onNotification: (item) => received.push(item.id),
        onStatusChange: (status) => statuses.push(status),
      },
    );

    vi.advanceTimersByTime(100);
    handle.close();
    handle.close();
    vi.advanceTimersByTime(5000);

    expect(received).toEqual([]);
    expect(statuses).toEqual(["connecting", "connected", "closed"]);
  });
});

describe("live notification channel", () => {
  it("opens a uni socket, forwards envelopes, and closes cleanly", () => {
    const handlers: Record<string, (payload?: unknown) => void> = {};
    const closeMock = vi.fn();
    const connectSocketMock = vi.fn((_options: { url: string; complete?: () => void }) => ({
      onOpen: (cb: () => void) => {
        handlers.open = cb;
      },
      onMessage: (cb: (event: { data: string }) => void) => {
        handlers.message = cb as (payload?: unknown) => void;
      },
      onClose: (cb: () => void) => {
        handlers.close = cb;
      },
      onError: (cb: () => void) => {
        handlers.error = cb;
      },
      close: closeMock,
    }));
    vi.stubGlobal("uni", { connectSocket: connectSocketMock });

    const statuses: NotificationSocketStatus[] = [];
    const received: string[] = [];
    const handle = connectNotificationChannel(
      {
        mode: "live",
        api_base_url: "https://trmx.example/api/v1",
        access_token: "token-abc",
      },
      {
        onNotification: (item) => received.push(item.id),
        onStatusChange: (status) => statuses.push(status),
      },
    );

    expect(connectSocketMock).toHaveBeenCalledTimes(1);
    const connectArgs = connectSocketMock.mock.calls[0][0];
    expect(connectArgs.url).toContain("wss://trmx.example/api/v1/ws/notifications");
    expect(connectArgs.url).toContain("token=token-abc");

    handlers.open?.();
    handlers.message?.({
      data: JSON.stringify({ type: "notification.new", data: buildDto({ id: "live-9" }) }),
    });
    handlers.message?.({ data: "broken-json" });
    handle.close();

    expect(received).toEqual(["live-9"]);
    expect(statuses).toEqual(["connecting", "connected", "closed"]);
    expect(closeMock).toHaveBeenCalled();

    vi.unstubAllGlobals();
  });
});
