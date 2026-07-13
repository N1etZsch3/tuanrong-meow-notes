import { describe, expect, it } from "vitest";

import messagesPageSource from "../../src/pages/messages/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";
import {
  NOTIFICATION_LABELS,
  countUnread,
  dismissNotification,
  extractLocalStates,
  filterNotifications,
  formatNotificationTime,
  indexLocalStates,
  markAllRead,
  markRead,
  markUnread,
  mergeIncomingNotifications,
  resolveNotificationChannel,
  selectNotifications,
  setLabel,
  sortNotifications,
  togglePinned,
  toNotificationView,
  type NotificationItemDto,
  type NotificationView,
} from "@/pages/messages/messages-page";
import { MOCK_NOTIFICATIONS, buildMockPushes } from "@/pages/messages/mock-notifications";

function buildDto(overrides: Partial<NotificationItemDto> = {}): NotificationItemDto {
  return {
    id: "ntf-1",
    notification_type: "new_task",
    title: "新任务已发布",
    content: "白敬亭喂食任务已发布",
    related_type: "task",
    related_id: "task-1",
    is_read: false,
    read_at: null,
    created_at: "2026-07-13T08:00:00+08:00",
    ...overrides,
  };
}

function buildView(overrides: Partial<NotificationView> = {}): NotificationView {
  return {
    ...toNotificationView(buildDto()),
    ...overrides,
  };
}

describe("messages page notification model", () => {
  it("maps notification types to display channels with badges", () => {
    expect(resolveNotificationChannel("new_task")).toMatchObject({
      title: "任务系统",
      badge: "官方",
    });
    expect(resolveNotificationChannel("task_checkin")).toMatchObject({
      title: "喂食提醒",
      badge: "系统",
    });
    expect(resolveNotificationChannel("medicine_updated")).toMatchObject({
      title: "药品管理",
      badge: "管理",
    });
    expect(resolveNotificationChannel("supply_updated")).toMatchObject({
      title: "物资通知",
    });
    expect(resolveNotificationChannel("announcement")).toMatchObject({
      title: "系统公告",
      badge: "官方",
    });
    expect(resolveNotificationChannel("cat_health_abnormal")).toMatchObject({
      title: "猫咪健康",
    });
  });

  it("sorts pinned notifications first then by newest created time", () => {
    const older = buildView({ id: "a", created_at: "2026-07-11T08:00:00+08:00" });
    const newer = buildView({ id: "b", created_at: "2026-07-12T08:00:00+08:00" });
    const pinnedOld = buildView({
      id: "c",
      created_at: "2026-07-01T08:00:00+08:00",
      is_pinned: true,
    });

    expect(sortNotifications([older, newer, pinnedOld]).map((item) => item.id)).toEqual([
      "c",
      "b",
      "a",
    ]);
  });

  it("filters the unread tab and always hides dismissed items", () => {
    const unread = buildView({ id: "a" });
    const read = buildView({ id: "b", is_read: true });
    const dismissed = buildView({ id: "c", is_dismissed: true });

    expect(filterNotifications([unread, read, dismissed], "all").map((i) => i.id)).toEqual([
      "a",
      "b",
    ]);
    expect(filterNotifications([unread, read, dismissed], "unread").map((i) => i.id)).toEqual([
      "a",
    ]);
    expect(countUnread([unread, read, dismissed])).toBe(1);
  });

  it("merges websocket pushes without dropping local marks", () => {
    const existing = buildView({ id: "a", is_pinned: true, label_key: "important" });
    const merged = mergeIncomingNotifications(
      [existing],
      [buildDto({ id: "a", content: "更新后的内容" }), buildDto({ id: "b" })],
    );

    const refreshed = merged.find((item) => item.id === "a");
    expect(refreshed?.content).toBe("更新后的内容");
    expect(refreshed?.is_pinned).toBe(true);
    expect(refreshed?.label_key).toBe("important");
    expect(merged.map((item) => item.id).sort()).toEqual(["a", "b"]);
  });

  it("marks read, unread, and clears all unread while keeping dismissed intact", () => {
    const items = [
      buildView({ id: "a" }),
      buildView({ id: "b" }),
      buildView({ id: "c", is_dismissed: true }),
    ];

    const afterRead = markRead(items, "a");
    expect(afterRead.find((i) => i.id === "a")?.is_read).toBe(true);
    expect(afterRead.find((i) => i.id === "a")?.read_at).toBeTruthy();

    const afterUnread = markUnread(afterRead, "a");
    expect(afterUnread.find((i) => i.id === "a")?.is_read).toBe(false);
    expect(afterUnread.find((i) => i.id === "a")?.read_at).toBeNull();

    const cleared = markAllRead(afterUnread);
    expect(countUnread(cleared)).toBe(0);
    expect(cleared.find((i) => i.id === "c")?.is_dismissed).toBe(true);
  });

  it("toggles pin, assigns labels, and dismisses via the done action", () => {
    const items = [buildView({ id: "a" })];

    const pinned = togglePinned(items, "a");
    expect(pinned[0].is_pinned).toBe(true);
    expect(togglePinned(pinned, "a")[0].is_pinned).toBe(false);

    const labeled = setLabel(items, "a", "follow_up");
    expect(labeled[0].label_key).toBe("follow_up");
    expect(setLabel(labeled, "a", "follow_up")[0].label_key).toBeNull();
    expect(NOTIFICATION_LABELS.follow_up.text).toBe("待跟进");

    const dismissed = dismissNotification(items, "a");
    expect(dismissed[0].is_dismissed).toBe(true);
    expect(dismissed[0].is_read).toBe(true);
    expect(selectNotifications(dismissed, "all")).toEqual([]);
  });

  it("persists only non-default local marks and restores them by id", () => {
    const items = [
      buildView({ id: "a", is_pinned: true }),
      buildView({ id: "b" }),
      buildView({ id: "c", is_dismissed: true, label_key: "resolved" }),
    ];

    const stored = extractLocalStates(items);
    expect(stored.map((entry) => entry.id).sort()).toEqual(["a", "c"]);

    const index = indexLocalStates(stored);
    expect(index.a.is_pinned).toBe(true);
    expect(index.c.is_dismissed).toBe(true);
    expect(index.c.label_key).toBe("resolved");
    expect(indexLocalStates(null)).toEqual({});
  });

  it("formats notification times relative to now", () => {
    const now = new Date("2026-07-13T09:12:00+08:00").getTime();
    expect(formatNotificationTime("2026-07-13T09:11:40+08:00", now)).toBe("刚刚");
    expect(formatNotificationTime("2026-07-13T08:50:00+08:00", now)).toBe("22分钟前");
    expect(formatNotificationTime("2026-07-13T01:05:00+08:00", now)).toBe("今天 01:05");
    expect(formatNotificationTime("2026-07-12T22:00:00+08:00", now)).toBe("昨天");
    expect(formatNotificationTime("2026-07-05T10:00:00+08:00", now)).toBe("7月5日");
    expect(formatNotificationTime("2025-12-31T10:00:00+08:00", now)).toBe("2025/12/31");
    expect(formatNotificationTime("not-a-date", now)).toBe("");
  });

  it("ships mock data aligned with the notification contract", () => {
    expect(MOCK_NOTIFICATIONS.length).toBeGreaterThanOrEqual(6);
    for (const item of MOCK_NOTIFICATIONS) {
      expect(item.id).toBeTruthy();
      expect(item.created_at).toBeTruthy();
      expect(typeof item.is_read).toBe("boolean");
      expect(resolveNotificationChannel(item.notification_type).title).toBeTruthy();
    }
    const pushes = buildMockPushes(Date.now());
    expect(pushes.length).toBeGreaterThan(0);
    for (const push of pushes) {
      expect(push.delay_ms).toBeGreaterThan(0);
      expect(push.notification.is_read).toBe(false);
    }
  });
});

describe("messages page wiring", () => {
  it("registers the messages page as the second tab titled 喵息", () => {
    expect(pagesJson).toContain("pages/messages/index");
    expect(pagesJson).toContain("喵息");
    const tabBarSection = pagesJson.slice(pagesJson.indexOf('"tabBar"'));
    expect(tabBarSection).toContain("pages/messages/index");
    expect(tabBarSection).not.toContain("pages/cats/index");
  });

  it("keeps the messages page on the shared background with the app tab bar", () => {
    expect(messagesPageSource).toContain("背景.jpg");
    expect(messagesPageSource).toContain('<AppTabBar active-key="messages" />');
    expect(messagesPageSource).toContain("喵息");
    expect(messagesPageSource).toContain("系统通知与任务动态");
    expect(messagesPageSource).toContain("userStore.ensureFreshAccessToken()");
    expect(messagesPageSource).toContain("var(--catmap-page-title-top, 92rpx)");
  });

  it("wires the mock websocket channel and unread management flows", () => {
    expect(messagesPageSource).toContain("connectNotificationChannel");
    expect(messagesPageSource).toContain('mode: "mock"');
    expect(messagesPageSource).toContain("buildMockPushes");
    expect(messagesPageSource).toContain("清除全部未读");
    expect(messagesPageSource).toContain("markAllRead");
    expect(messagesPageSource).toContain("@longpress");
    expect(messagesPageSource).toContain("标为未读");
    expect(messagesPageSource).toContain("置顶");
    expect(messagesPageSource).toContain("标签");
    expect(messagesPageSource).toContain("完成");
    expect(messagesPageSource).toContain("@touchstart");
    expect(messagesPageSource).toContain("swipe-action");
    expect(messagesPageSource).toContain("消息空荡荡的.svg");
    expect(messagesPageSource).toContain("暂无消息");
  });

  it("uses the prepared 喵息 channel avatars", () => {
    expect(messagesPageSource).toContain("素材/svg/喵息/猫粮盆.svg");
    expect(messagesPageSource).toContain("素材/svg/喵息/药品.svg");
    expect(messagesPageSource).toContain("素材/svg/喵息/消息.svg");
    expect(messagesPageSource).toContain("素材/svg/喵记/任务.svg");
    expect(messagesPageSource).toContain("素材/svg/喵记/物资仓库.svg");
  });
});
