/**
 * 通知实时通道（WebSocket）。
 *
 * 设计目标：页面只面向 NotificationChannelHandle 编程，底层可在
 * mock 驱动与 uni.connectSocket 真实驱动之间切换。
 *
 * 约定的服务端消息信封（后端未实现，先按此契约演进）：
 *   { "type": "notification.new", "data": NotificationItemDto }
 *   { "type": "notification.read_all" }
 *   { "type": "ping" } / { "type": "pong" }
 *
 * 真实通道路径约定为 `${wss(baseUrl)}/ws/notifications?token=<accessToken>`，
 * 由 buildNotificationSocketUrl 从 HTTP API base 推导。
 */

import type { NotificationItemDto } from "@/pages/messages/messages-page";

export type NotificationSocketStatus = "connecting" | "connected" | "closed";

export interface NotificationChannelCallbacks {
  onNotification: (item: NotificationItemDto) => void;
  onStatusChange?: (status: NotificationSocketStatus) => void;
}

export interface NotificationChannelHandle {
  close: () => void;
}

/** 把 http(s) 的 API base 换算成 ws(s) 通知端点。 */
export function buildNotificationSocketUrl(apiBaseUrl: string): string {
  const trimmed = apiBaseUrl.replace(/\/+$/, "");
  const wsBase = trimmed
    .replace(/^https:\/\//i, "wss://")
    .replace(/^http:\/\//i, "ws://");
  return `${wsBase}/ws/notifications`;
}

interface ServerEnvelope {
  type?: string;
  data?: unknown;
}

/** 解析服务端信封，仅接受合法的通知负载。 */
export function parseNotificationEnvelope(raw: unknown): NotificationItemDto | null {
  let envelope: ServerEnvelope | null = null;
  if (typeof raw === "string") {
    try {
      envelope = JSON.parse(raw) as ServerEnvelope;
    } catch {
      return null;
    }
  } else if (raw && typeof raw === "object") {
    envelope = raw as ServerEnvelope;
  }
  if (!envelope || envelope.type !== "notification.new") {
    return null;
  }
  const data = envelope.data as Partial<NotificationItemDto> | undefined;
  if (
    !data ||
    typeof data.id !== "string" ||
    typeof data.notification_type !== "string" ||
    typeof data.created_at !== "string"
  ) {
    return null;
  }
  return {
    id: data.id,
    notification_type: data.notification_type,
    title: typeof data.title === "string" ? data.title : "",
    content: typeof data.content === "string" ? data.content : "",
    related_type: data.related_type ?? null,
    related_id: data.related_id ?? null,
    is_read: Boolean(data.is_read),
    read_at: data.read_at ?? null,
    created_at: data.created_at,
  } as NotificationItemDto;
}

export interface MockChannelOptions {
  mode: "mock";
  /** 需要按序推送的通知（带延迟）。 */
  pushes: Array<{ delay_ms: number; notification: NotificationItemDto }>;
  /** 模拟建连耗时，默认 700ms。 */
  connect_delay_ms?: number;
}

export interface LiveChannelOptions {
  mode: "live";
  api_base_url: string;
  access_token: string;
}

export type NotificationChannelOptions = MockChannelOptions | LiveChannelOptions;

/**
 * 打开通知通道。返回句柄用于关闭；重复 close 是安全的。
 */
export function connectNotificationChannel(
  options: NotificationChannelOptions,
  callbacks: NotificationChannelCallbacks,
): NotificationChannelHandle {
  if (options.mode === "mock") {
    return connectMockChannel(options, callbacks);
  }
  return connectLiveChannel(options, callbacks);
}

function connectMockChannel(
  options: MockChannelOptions,
  callbacks: NotificationChannelCallbacks,
): NotificationChannelHandle {
  const timers: Array<ReturnType<typeof setTimeout>> = [];
  let closed = false;

  callbacks.onStatusChange?.("connecting");

  timers.push(
    setTimeout(() => {
      if (closed) {
        return;
      }
      callbacks.onStatusChange?.("connected");
      for (const push of options.pushes) {
        timers.push(
          setTimeout(() => {
            if (!closed) {
              callbacks.onNotification(push.notification);
            }
          }, push.delay_ms),
        );
      }
    }, options.connect_delay_ms ?? 700),
  );

  return {
    close: () => {
      if (closed) {
        return;
      }
      closed = true;
      for (const timer of timers) {
        clearTimeout(timer);
      }
      callbacks.onStatusChange?.("closed");
    },
  };
}

function connectLiveChannel(
  options: LiveChannelOptions,
  callbacks: NotificationChannelCallbacks,
): NotificationChannelHandle {
  let closed = false;

  callbacks.onStatusChange?.("connecting");

  const task = uni.connectSocket({
    url: `${buildNotificationSocketUrl(options.api_base_url)}?token=${encodeURIComponent(options.access_token)}`,
    complete: () => {
      // uni 类型要求至少一个回调才返回 SocketTask。
    },
  });

  task.onOpen(() => {
    if (!closed) {
      callbacks.onStatusChange?.("connected");
    }
  });
  task.onMessage((event) => {
    if (closed) {
      return;
    }
    const item = parseNotificationEnvelope(event.data);
    if (item) {
      callbacks.onNotification(item);
    }
  });
  task.onClose(() => {
    if (!closed) {
      callbacks.onStatusChange?.("closed");
    }
  });
  task.onError(() => {
    if (!closed) {
      callbacks.onStatusChange?.("closed");
    }
  });

  return {
    close: () => {
      if (closed) {
        return;
      }
      closed = true;
      try {
        task.close({ code: 1000 });
      } catch {
        // 已断开时 close 可能抛错，忽略。
      }
      callbacks.onStatusChange?.("closed");
    },
  };
}
