import { describe, expect, it } from "vitest";

import messagesPageSource from "../../src/pages/messages/index.vue?raw";
import messageCardSwipeSource from "../../src/pages/messages/message-card-swipe.wxs?raw";
import pagesJson from "../../src/pages.json?raw";
import {
  activateCardLongPress,
  canActivateCardLongPress,
  isCardGestureOwner,
  resolveCardSwipe,
  shouldBlockMessageRefresh,
  shouldDeferMessageListUpdate,
  shouldSuppressCardTap,
  startCardGesture,
  updateCardGesture,
} from "@/pages/messages/message-card-gesture";
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

describe("message card gesture arbitration", () => {
  it("keeps ordinary finger jitter eligible for a long press and a tap", () => {
    const started = startCardGesture("a", { x: 100, y: 200 });
    const updated = updateCardGesture(started, { x: 103, y: 202 }).state;

    expect(updated.intent).toBe("pending");
    expect(updated.didMove).toBe(false);
    expect(canActivateCardLongPress(updated, "a", { x: 103, y: 202 })).toBe(true);
    expect(shouldSuppressCardTap(updated)).toBe(false);
  });

  it("rejects a native long press once the finger has started drifting", () => {
    const started = startCardGesture("a", { x: 100, y: 200 });
    const updated = updateCardGesture(started, { x: 111, y: 200 }).state;

    expect(updated.intent).toBe("horizontal");
    expect(updated.didMove).toBe(true);
    expect(canActivateCardLongPress(updated, "a", { x: 111, y: 200 })).toBe(false);
    expect(canActivateCardLongPress(started, "a", { x: 111, y: 200 })).toBe(false);
    expect(shouldSuppressCardTap(updated)).toBe(true);
  });

  it("locks a deliberate horizontal move to swipe and suppresses tap", () => {
    const started = startCardGesture("a", { x: 180, y: 300 });
    const update = updateCardGesture(started, { x: 150, y: 303 });

    expect(update.state.intent).toBe("horizontal");
    expect(update.deltaX).toBe(-30);
    expect(canActivateCardLongPress(update.state, "a")).toBe(false);
    expect(shouldSuppressCardTap(update.state)).toBe(true);
  });

  it("resolves swipe snap state from the same end point without per-frame Vue updates", () => {
    const closed = startCardGesture("a", { x: 300, y: 200 });
    expect(resolveCardSwipe(closed, { x: 230, y: 202 }, 180).open).toBe(false);
    expect(resolveCardSwipe(closed, { x: 210, y: 202 }, 180).open).toBe(true);

    const opened = startCardGesture(
      "a",
      { x: 120, y: 200 },
      { startedOpen: true },
    );
    expect(resolveCardSwipe(opened, { x: 230, y: 202 }, 180).open).toBe(false);
    expect(resolveCardSwipe(opened, { x: 230, y: 202 }, 180, { cancelled: true }).open).toBe(
      true,
    );
  });

  it("locks vertical scrolling away from swipe and long press", () => {
    const started = startCardGesture("a", { x: 180, y: 300 });
    const update = updateCardGesture(started, { x: 183, y: 330 });

    expect(update.state.intent).toBe("vertical");
    expect(canActivateCardLongPress(update.state, "a")).toBe(false);
    expect(shouldSuppressCardTap(update.state)).toBe(true);
  });

  it("consumes the first touch on another card when a swipe is already open", () => {
    const consumed = startCardGesture(
      "b",
      { x: 120, y: 220 },
      { consume: true, startedOpen: false },
    );
    const updated = updateCardGesture(consumed, { x: 80, y: 220 }).state;

    expect(updated.intent).toBe("consumed");
    expect(canActivateCardLongPress(updated, "b")).toBe(false);
    expect(shouldSuppressCardTap(updated)).toBe(true);
  });

  it("makes an accepted long press exclusive from the following tap", () => {
    const started = startCardGesture("a", { x: 100, y: 200 });
    const longPressed = activateCardLongPress(started);

    expect(longPressed.intent).toBe("longpress");
    expect(canActivateCardLongPress(longPressed, "a")).toBe(false);
    expect(shouldSuppressCardTap(longPressed)).toBe(true);
  });

  it("keeps one touch bound to its original message card", () => {
    const started = startCardGesture("a", { x: 100, y: 200, touchId: 7 });

    expect(isCardGestureOwner(started, "a", 7)).toBe(true);
    expect(isCardGestureOwner(started, "b", 7)).toBe(false);
    expect(isCardGestureOwner(started, "a", 8)).toBe(false);
  });

  it("keeps live list updates deferred while swipe actions stay open", () => {
    expect(
      shouldDeferMessageListUpdate({
        gestureActive: false,
        longPressPending: false,
        menuOpen: false,
        swipeOpen: true,
        swipeDragging: false,
      }),
    ).toBe(true);
    expect(
      shouldDeferMessageListUpdate({
        gestureActive: false,
        longPressPending: false,
        menuOpen: false,
        swipeOpen: false,
        swipeDragging: false,
      }),
    ).toBe(false);
  });

  it("blocks pull-to-refresh only for card-owned horizontal interactions", () => {
    const base = {
      longPressPending: false,
      menuOpen: false,
      swipeOpen: false,
      swipeDragging: false,
    };

    expect(shouldBlockMessageRefresh({ ...base, gestureIntent: "horizontal" })).toBe(true);
    expect(shouldBlockMessageRefresh({ ...base, gestureIntent: "vertical" })).toBe(false);
    expect(shouldBlockMessageRefresh({ ...base, gestureIntent: null, swipeOpen: true })).toBe(true);
  });
});

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
    const readAt = "2026-07-15T12:20:00+08:00";
    const existing = buildView({
      id: "a",
      is_read: true,
      read_at: readAt,
      is_pinned: true,
      label_key: "important",
    });
    const merged = mergeIncomingNotifications(
      [existing],
      [buildDto({ id: "a", content: "更新后的内容" }), buildDto({ id: "b" })],
    );

    const refreshed = merged.find((item) => item.id === "a");
    expect(refreshed?.content).toBe("更新后的内容");
    expect(refreshed?.is_read).toBe(true);
    expect(refreshed?.read_at).toBe(readAt);
    expect(refreshed?.is_pinned).toBe(true);
    expect(refreshed?.label_key).toBe("important");
    expect(merged.map((item) => item.id).sort()).toEqual(["a", "b"]);
  });

  it("restores persisted read state when a websocket message returns after page re-entry", () => {
    const readAt = "2026-07-15T12:21:00+08:00";
    const stored = indexLocalStates(
      extractLocalStates([buildView({ id: "live-a", is_read: true, read_at: readAt })]),
    );

    const merged = mergeIncomingNotifications(
      [buildView({ id: "live-a", is_read: false, read_at: null })],
      [buildDto({ id: "live-a", is_read: false, read_at: null })],
      stored,
    );

    expect(merged[0].is_read).toBe(true);
    expect(merged[0].read_at).toBe(readAt);
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

  it("persists read state across page re-entry together with local marks", () => {
    const readAt = "2026-07-15T12:20:00+08:00";
    const items = [
      buildView({ id: "a", is_pinned: true, is_read: true, read_at: readAt }),
      buildView({ id: "b" }),
      buildView({ id: "c", is_dismissed: true, label_key: "resolved" }),
    ];

    const stored = extractLocalStates(items);
    expect(stored.map((entry) => entry.id).sort()).toEqual(["a", "b", "c"]);

    const index = indexLocalStates(stored);
    expect(index.a.is_pinned).toBe(true);
    expect(index.a.is_read).toBe(true);
    expect(index.a.read_at).toBe(readAt);
    expect(index.b.is_read).toBe(false);
    expect(index.c.is_dismissed).toBe(true);
    expect(index.c.label_key).toBe("resolved");
    expect(toNotificationView(buildDto({ id: "a" }), index.a).is_read).toBe(true);
    expect(
      toNotificationView(buildDto({ id: "b", is_read: true, read_at: readAt }), index.b).is_read,
    ).toBe(false);
    const legacy = indexLocalStates([
      {
        id: "legacy",
        is_pinned: true,
        is_muted: false,
        is_dismissed: false,
        label_key: null,
      },
    ]);
    expect(legacy.legacy).not.toHaveProperty("is_read");
    expect(toNotificationView(buildDto({ id: "legacy", is_read: true }), legacy.legacy).is_read).toBe(
      true,
    );
    expect(indexLocalStates(null)).toEqual({});
  });

  it("publishes unread changes for the shared bottom tab indicator", () => {
    expect(messagesPageSource).toContain("publishMessagesUnreadIndicator");
    expect(messagesPageSource).toContain("publishMessagesUnreadIndicator(countUnread(next) > 0)");
    expect(messagesPageSource).toContain("setMessages(next, true)");
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
    expect(messagesPageSource).toContain("markAllRead");
    expect(messagesPageSource).toContain("@longpress");
    expect(messagesPageSource).toContain('@longpress="handleCardLongPress(msg, $event)"');
    expect(messagesPageSource).toContain('@touchstart="handleCardTouchStart(msg.id, $event)"');
    expect(messagesPageSource).toContain(
      '@touchmove.capture="handleCardTouchMove(msg.id, $event)"',
    );
    expect(messagesPageSource).toContain('@touchend="handleCardTouchEnd(msg.id, $event)"');
    expect(messagesPageSource).toContain('@tap="handleCardTap(msg)"');
    expect(messagesPageSource).toContain("consumeSuppressedCardTap");
    expect(messagesPageSource).toContain("canActivateCardLongPress");
    expect(messagesPageSource).toContain("deferredIncomingNotifications");
    expect(messagesPageSource).toContain("hasBlockingCardInteraction()");
    expect(messagesPageSource).toContain("messageSwipe.touchmove");
    expect(messagesPageSource).toContain("scroll-y");
    expect(messagesPageSource).toContain(':enhanced="true"');
    expect(messagesPageSource).toContain(':refresher-enabled="!isSwipeRefreshBlocked"');
    expect(messagesPageSource).toContain("mergeIncomingNotifications(messages.value, base)");
    expect(messagesPageSource).toContain("async function applySwipeListMutation");
    expect(messagesPageSource).toContain("await nextTick()");
    expect(messagesPageSource).toContain("swipeMutationPending");
    expect(messagesPageSource).toContain(".messages-scroll::-webkit-scrollbar");
    expect(messagesPageSource).toContain("标为未读");
    expect(messagesPageSource).toContain("置顶");
    expect(messagesPageSource).toContain("标签");
    expect(messagesPageSource).toContain("完成");
    expect(messagesPageSource).toContain("@touchstart");
    expect(messagesPageSource).toContain("swipe-action");
    expect(messagesPageSource).toContain("消息空荡荡的.svg");
    expect(messagesPageSource).toContain("暂无消息");
  });

  it("marks a tapped message read only after detail navigation succeeds", () => {
    const handlerStart = messagesPageSource.indexOf("function handleCardTap");
    const handlerEnd = messagesPageSource.indexOf("function handleCardLongPress", handlerStart);
    const handlerSource = messagesPageSource.slice(handlerStart, handlerEnd);
    const navigateIndex = handlerSource.indexOf("uni.navigateTo");
    const successIndex = handlerSource.indexOf("success: () => {", navigateIndex);
    const markReadIndex = handlerSource.indexOf("applyMessages(markRead", navigateIndex);

    expect(handlerStart).toBeGreaterThanOrEqual(0);
    expect(handlerEnd).toBeGreaterThan(handlerStart);
    expect(navigateIndex).toBeGreaterThanOrEqual(0);
    expect(successIndex).toBeGreaterThan(navigateIndex);
    expect(markReadIndex).toBeGreaterThan(successIndex);
    expect(handlerSource.slice(0, navigateIndex)).not.toContain("markRead");
  });

  it("pre-renders swipe actions and moves the foreground card in the WXS view layer", () => {
    expect(messagesPageSource).toContain(
      '<script module="messageSwipe" lang="wxs" src="./message-card-swipe.wxs"></script>',
    );
    expect(messagesPageSource).toContain(':change:swipeViewState="messageSwipe.sync"');
    expect(messagesPageSource).toContain('class="swipe-actions"');
    expect(messagesPageSource).not.toContain('v-if="isCellSwiping(msg.id)"');
    expect(messagesPageSource).not.toContain(':disabled="!canUseSwipeAction(msg.id)"');
    expect(messagesPageSource).not.toContain("swipeActionsReadyId");
    expect(messagesPageSource).not.toContain("swipeDragX");
    expect(messageCardSwipeSource).toContain("instance.setStyle({");
    expect(messageCardSwipeSource).toContain("transform: 'translateX('");
    expect(messageCardSwipeSource).toContain("function touchmove(event, ownerInstance)");
    expect(messageCardSwipeSource).toContain("function parseViewState(value)");
    expect(messagesPageSource).toContain('.join("|")');
    expect(messageCardSwipeSource).toContain("return false;");
    expect(messageCardSwipeSource).not.toContain("callOwner");
    expect(messageCardSwipeSource).not.toContain("longpress");
    expect(messagesPageSource).not.toContain("defineExpose");
  });

  it("opens unread cleanup from a long press without rendering the old clear bar", () => {
    expect(messagesPageSource).toContain('@longpress="openClearConfirm"');
    expect(messagesPageSource).toContain('class="unread-sheet-overlay"');
    expect(messagesPageSource).toContain("确定清除全部未读消息");
    expect(messagesPageSource).toContain("清除未读");
    expect(messagesPageSource).toContain('activeTab.value !== "unread"');
    expect(messagesPageSource).not.toContain('class="clear-bar"');
    expect(messagesPageSource).not.toContain("clear-bar-button");
    expect(messagesPageSource).not.toContain("clearSweepIcon");
  });

  it("uses the prepared 喵息 channel avatars", () => {
    expect(messagesPageSource).toContain("素材/svg/喵息/猫粮盆.svg");
    expect(messagesPageSource).toContain("素材/svg/喵息/药品.svg");
    expect(messagesPageSource).toContain("素材/svg/喵息/消息.svg");
    expect(messagesPageSource).toContain("素材/svg/喵记/任务.svg");
    expect(messagesPageSource).toContain("素材/svg/喵记/物资仓库.svg");
  });
});
