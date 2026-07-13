<template>
  <view class="messages-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />

    <view class="messages-inner" :class="{ 'is-dimmed': isOverlayActive }">
      <view class="messages-fixed">
        <view class="page-title">
          <view class="page-title-row">
            <text class="page-title-text">喵息</text>
            <image class="page-title-icon" :src="titleMascotIcon" mode="aspectFit" />
          </view>
          <view class="page-title-subrow">
            <text class="page-title-subtitle">系统通知与任务动态</text>
            <view class="live-status" :class="`live-${socketStatus}`">
              <view class="live-dot" />
              <text class="live-text">{{ socketStatusLabel }}</text>
            </view>
          </view>
        </view>

        <view class="tab-row">
          <view class="segment">
            <button
              class="segment-item"
              :class="{ 'is-active': activeTab === 'all' }"
              @tap="switchTab('all')"
            >
              消息
            </button>
            <button
              class="segment-item"
              :class="{ 'is-active': activeTab === 'unread' }"
              @tap="switchTab('unread')"
            >
              <text>未读</text>
              <text v-if="unreadCount > 0" class="segment-badge">{{ unreadCount }}</text>
            </button>
          </view>
        </view>

        <view class="clear-bar" :class="{ 'is-visible': showClearBar }">
          <button class="clear-bar-button" hover-class="clear-bar-hover" @tap="openClearConfirm">
            <image class="clear-bar-icon" :src="clearSweepIcon" mode="aspectFit" />
            <text class="clear-bar-text">清除全部未读</text>
            <text class="clear-bar-count">共 {{ unreadCount }} 条</text>
          </button>
        </view>
      </view>

      <scroll-view
        class="messages-scroll"
        scroll-y
        refresher-enabled
        :refresher-triggered="isRefreshing"
        :show-scrollbar="false"
        @refresherrefresh="refreshMessages"
      >
        <view class="messages-body">
          <view v-if="visibleMessages.length === 0" class="empty-card">
            <image class="empty-illustration" :src="emptyMessagesIllustration" mode="aspectFit" />
            <text class="empty-title">{{ emptyTitle }}</text>
            <text class="empty-desc">{{ emptyDesc }}</text>
          </view>

          <view v-else class="message-list">
            <view
              v-for="msg in visibleMessages"
              :key="msg.id"
              class="swipe-cell"
              :class="{ 'is-swiping': isCellSwiping(msg.id) }"
            >
              <view v-if="isCellSwiping(msg.id)" class="swipe-actions">
                <button class="swipe-action action-read" @tap="handleSwipeRead(msg)">
                  <text class="swipe-action-icon">{{ msg.is_read ? "◌" : "◉" }}</text>
                  <text class="swipe-action-text">{{ msg.is_read ? "未读" : "已读" }}</text>
                </button>
                <button class="swipe-action action-pin" @tap="handleSwipePin(msg)">
                  <text class="swipe-action-icon">↑</text>
                  <text class="swipe-action-text">{{ msg.is_pinned ? "取消" : "置顶" }}</text>
                </button>
                <button class="swipe-action action-done" @tap="handleSwipeDone(msg)">
                  <text class="swipe-action-icon">✓</text>
                  <text class="swipe-action-text">完成</text>
                </button>
              </view>

              <view
                :id="`msg-card-${msg.id}`"
                class="message-card"
                :class="{
                  'is-unread': !msg.is_read,
                  'is-pinned': msg.is_pinned,
                  'is-dragging': swipeDraggingId === msg.id,
                }"
                :style="cardTransformStyle(msg.id)"
                @touchstart="onCardTouchStart(msg.id, $event)"
                @touchmove="onCardTouchMove(msg.id, $event)"
                @touchend="onCardTouchEnd(msg.id)"
                @touchcancel="onCardTouchEnd(msg.id)"
                @longpress="openActionMenu(msg)"
                @tap="handleCardTap(msg)"
              >
                <view class="card-avatar" :class="`avatar-${channelOf(msg).tone}`">
                  <image
                    class="card-avatar-icon"
                    :class="`avatar-icon-${channelOf(msg).icon_key}`"
                    :src="channelIcon(msg)"
                    mode="aspectFit"
                  />
                </view>
                <view class="card-main">
                  <view class="card-title-row">
                    <text class="card-source">{{ channelOf(msg).title }}</text>
                    <text class="card-badge" :class="`badge-${channelOf(msg).tone}`">
                      {{ channelOf(msg).badge }}
                    </text>
                    <text
                      v-if="labelOf(msg)"
                      class="card-label"
                      :class="`label-${labelOf(msg)!.tone}`"
                    >
                      {{ labelOf(msg)!.text }}
                    </text>
                    <text class="card-time">{{ formatTime(msg.created_at) }}</text>
                  </view>
                  <view class="card-content-row">
                    <text class="card-content">{{ msg.content }}</text>
                    <view v-if="!msg.is_read" class="unread-dot" />
                  </view>
                </view>
                <view v-if="msg.is_pinned" class="pin-fold" />
              </view>
            </view>

            <view class="list-footer">
              <text class="footer-paw">🐾</text>
              <text>没有更多了～</text>
              <text class="footer-paw">🐾</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <view
      v-if="menuTarget"
      class="press-overlay"
      @tap="closeActionMenu"
      @touchmove.stop.prevent
    >
      <view class="press-ghost" :style="ghostStyle" @tap.stop>
        <view class="message-card is-elevated" :class="{ 'is-unread': !menuTarget.is_read }">
          <view class="card-avatar" :class="`avatar-${channelOf(menuTarget).tone}`">
            <image
              class="card-avatar-icon"
              :class="`avatar-icon-${channelOf(menuTarget).icon_key}`"
              :src="channelIcon(menuTarget)"
              mode="aspectFit"
            />
          </view>
          <view class="card-main">
            <view class="card-title-row">
              <text class="card-source">{{ channelOf(menuTarget).title }}</text>
              <text class="card-badge" :class="`badge-${channelOf(menuTarget).tone}`">
                {{ channelOf(menuTarget).badge }}
              </text>
              <text
                v-if="labelOf(menuTarget)"
                class="card-label"
                :class="`label-${labelOf(menuTarget)!.tone}`"
              >
                {{ labelOf(menuTarget)!.text }}
              </text>
              <text class="card-time">{{ formatTime(menuTarget.created_at) }}</text>
            </view>
            <view class="card-content-row">
              <text class="card-content card-content-full">{{ menuTarget.content }}</text>
              <view v-if="!menuTarget.is_read" class="unread-dot" />
            </view>
          </view>
          <view v-if="menuTarget.is_pinned" class="pin-fold" />
        </view>
      </view>

      <view class="press-menu" :style="menuStyle" @tap.stop>
        <button class="menu-item" hover-class="menu-item-hover" @tap="handleMenuPin">
          <text class="menu-item-text">{{ menuTarget.is_pinned ? "取消置顶" : "置顶" }}</text>
          <text class="menu-item-icon">{{ menuTarget.is_pinned ? "↓" : "↑" }}</text>
        </button>
        <button class="menu-item" hover-class="menu-item-hover" @tap="handleMenuToggleRead">
          <text class="menu-item-text">{{ menuTarget.is_read ? "标为未读" : "标为已读" }}</text>
          <text class="menu-item-icon">{{ menuTarget.is_read ? "◌" : "◉" }}</text>
        </button>
        <button
          class="menu-item"
          :class="{ 'is-expanded': isLabelPickerOpen }"
          hover-class="menu-item-hover"
          @tap="toggleLabelPicker"
        >
          <text class="menu-item-text">标签</text>
          <text class="menu-item-icon">⚑</text>
        </button>
        <view class="label-picker" :class="{ 'is-open': isLabelPickerOpen }">
          <button
            v-for="label in labelOptions"
            :key="label.key"
            class="label-chip"
            :class="[
              `label-${label.tone}`,
              { 'is-selected': menuTarget.label_key === label.key },
            ]"
            @tap="handleMenuLabel(label.key)"
          >
            {{ label.text }}
          </button>
        </view>
        <view class="menu-divider" />
        <button class="menu-item menu-item-done" hover-class="menu-item-hover" @tap="handleMenuDone">
          <text class="menu-item-text">完成</text>
          <text class="menu-item-icon">✓</text>
        </button>
      </view>
    </view>

    <view v-if="isClearConfirmVisible" class="confirm-overlay" @tap="closeClearConfirm">
      <view class="confirm-card" @tap.stop>
        <view class="confirm-icon-ring">
          <image class="confirm-icon" :src="clearSweepIcon" mode="aspectFit" />
        </view>
        <text class="confirm-title">清除全部未读</text>
        <text class="confirm-desc">
          将 {{ unreadCount }} 条未读消息标记为已读，红点提醒会一并清除，消息仍会保留。
        </text>
        <view class="confirm-actions">
          <button class="confirm-button confirm-cancel" hover-class="confirm-button-hover" @tap="closeClearConfirm">
            取消
          </button>
          <button class="confirm-button confirm-primary" hover-class="confirm-button-hover" @tap="handleClearAllUnread">
            清除未读
          </button>
        </view>
      </view>
    </view>

    <AppTabBar active-key="messages" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onHide, onShow, onUnload } from "@dcloudio/uni-app";

import AppTabBar from "@/components/AppTabBar.vue";
import { LOGIN_ROUTE } from "@/services/app-startup";
import {
  connectNotificationChannel,
  type NotificationChannelHandle,
  type NotificationSocketStatus,
} from "@/services/notification-socket";
import { useUserStore } from "@/stores/user";

import {
  NOTIFICATION_LABELS,
  NOTIFICATION_LABEL_ORDER,
  countUnread,
  dismissNotification,
  extractLocalStates,
  formatNotificationTime,
  getNotificationLabel,
  indexLocalStates,
  markAllRead,
  markRead,
  markUnread,
  mergeIncomingNotifications,
  resolveNotificationChannel,
  selectNotifications,
  setLabel,
  togglePinned,
  toNotificationView,
  type MessagesTabKey,
  type NotificationChannelKey,
  type NotificationItemDto,
  type NotificationLabelKey,
  type NotificationView,
  type StoredLocalState,
} from "./messages-page";
import { MOCK_NOTIFICATIONS, buildMockPushes } from "./mock-notifications";

import loadingBackground from "../../../素材/加载页素材/背景.jpg";
import titleMascotIcon from "../../../素材/svg/萌猫/奶牛猫.svg";
import emptyMessagesIllustration from "../../../素材/svg/缺省页/消息空荡荡的.svg";
import clearSweepIcon from "../../../素材/svg/猫咪库/删除.svg";
import taskChannelIcon from "../../../素材/svg/喵记/任务.svg";
import feedingChannelIcon from "../../../素材/svg/喵息/猫粮盆.svg";
import medicineChannelIcon from "../../../素材/svg/喵息/药品.svg";
import supplyChannelIcon from "../../../素材/svg/喵记/物资仓库.svg";
import memberChannelIcon from "../../../素材/svg/喵息/消息.svg";
import catChannelIcon from "../../../素材/svg/默认/猫咪库.svg";

const LOCAL_STATE_STORAGE_KEY = "cat_map_messages_local_state_v1";

const CHANNEL_ICONS: Record<NotificationChannelKey, string> = {
  task: taskChannelIcon,
  feeding: feedingChannelIcon,
  medicine: medicineChannelIcon,
  supply: supplyChannelIcon,
  member: memberChannelIcon,
  cat: catChannelIcon,
  announcement: memberChannelIcon,
};

const SOCKET_STATUS_LABELS: Record<NotificationSocketStatus, string> = {
  connecting: "连接中",
  connected: "实时同步",
  closed: "已断开",
};

const userStore = useUserStore();

const messages = ref<NotificationView[]>([]);
const activeTab = ref<MessagesTabKey>("all");
const isRefreshing = ref(false);
const socketStatus = ref<NotificationSocketStatus>("closed");
const nowTick = ref(Date.now());

const menuTarget = ref<NotificationView | null>(null);
const isLabelPickerOpen = ref(false);
const ghostRect = ref<{ top: number; left: number; width: number; height: number } | null>(null);
const isClearConfirmVisible = ref(false);

const swipeOpenId = ref("");
const swipeDraggingId = ref("");
const swipeDragX = ref(0);

let channelHandle: NotificationChannelHandle | null = null;
let clockTimer: ReturnType<typeof setInterval> | null = null;
let touchStartX = 0;
let touchStartY = 0;
let touchDirection: "none" | "horizontal" | "vertical" = "none";

const labelOptions = NOTIFICATION_LABEL_ORDER.map((key) => NOTIFICATION_LABELS[key]);

const visibleMessages = computed(() => selectNotifications(messages.value, activeTab.value));
const unreadCount = computed(() => countUnread(messages.value));
const showClearBar = computed(() => activeTab.value === "unread" && unreadCount.value > 0);
const socketStatusLabel = computed(() => SOCKET_STATUS_LABELS[socketStatus.value]);
const isOverlayActive = computed(() => Boolean(menuTarget.value) || isClearConfirmVisible.value);

const emptyTitle = computed(() =>
  activeTab.value === "unread" ? "暂无未读消息" : "暂无消息",
);
const emptyDesc = computed(() =>
  activeTab.value === "unread"
    ? "红点都清干净啦，去消息里翻翻其他动态吧。"
    : "有新的任务提醒或系统通知时，会出现在这里。",
);

const ghostStyle = computed(() => {
  if (!ghostRect.value) {
    return "display: none;";
  }
  const rect = ghostRect.value;
  return `top: ${rect.top}px; left: ${rect.left}px; width: ${rect.width}px;`;
});

const menuStyle = computed(() => {
  if (!ghostRect.value) {
    return "display: none;";
  }
  const rect = ghostRect.value;
  const menuWidth = uni.upx2px(400);
  const estimatedMenuHeight = uni.upx2px(isLabelPickerOpen.value ? 520 : 420);
  const windowHeight = uni.getSystemInfoSync().windowHeight;
  const left = Math.max(rect.left, rect.left + rect.width - menuWidth);
  const below = rect.top + rect.height + uni.upx2px(16);
  const top =
    below + estimatedMenuHeight > windowHeight - uni.upx2px(180)
      ? Math.max(uni.upx2px(120), rect.top - estimatedMenuHeight - uni.upx2px(16))
      : below;
  return `top: ${top}px; left: ${left}px; width: ${menuWidth}px;`;
});

function channelOf(msg: NotificationView) {
  return resolveNotificationChannel(msg.notification_type);
}

function channelIcon(msg: NotificationView): string {
  return CHANNEL_ICONS[channelOf(msg).icon_key];
}

function labelOf(msg: NotificationView) {
  return getNotificationLabel(msg.label_key);
}

function formatTime(iso: string): string {
  return formatNotificationTime(iso, nowTick.value);
}

// ---- 本地状态持久化（mock 阶段） ----

function loadStoredLocalStates(): Record<string, ReturnType<typeof indexLocalStates>[string]> {
  try {
    const raw = uni.getStorageSync(LOCAL_STATE_STORAGE_KEY) as StoredLocalState[] | "";
    return indexLocalStates(Array.isArray(raw) ? raw : null);
  } catch {
    return {};
  }
}

function persistLocalStates() {
  try {
    uni.setStorageSync(LOCAL_STATE_STORAGE_KEY, extractLocalStates(messages.value));
  } catch {
    // 存储失败不影响页面运行。
  }
}

function applyMessages(next: NotificationView[]) {
  messages.value = next;
  persistLocalStates();
}

// ---- 数据装载与实时通道 ----

async function resolveAccessToken() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return null;
  }
  return accessToken;
}

function loadInitialMessages() {
  const locals = loadStoredLocalStates();
  const base = MOCK_NOTIFICATIONS.map((dto) => toNotificationView(dto, locals[dto.id]));
  messages.value = mergeIncomingNotifications(base, []);
}

function handleIncomingNotification(dto: NotificationItemDto) {
  messages.value = mergeIncomingNotifications(messages.value, [dto]);
}

function openChannel() {
  if (channelHandle) {
    return;
  }
  channelHandle = connectNotificationChannel(
    { mode: "mock", pushes: buildMockPushes(Date.now()) },
    {
      onNotification: handleIncomingNotification,
      onStatusChange: (status) => {
        socketStatus.value = status;
      },
    },
  );
}

function closeChannel() {
  channelHandle?.close();
  channelHandle = null;
}

async function refreshMessages() {
  isRefreshing.value = true;
  const locals = loadStoredLocalStates();
  const base = MOCK_NOTIFICATIONS.map((dto) => toNotificationView(dto, locals[dto.id]));
  messages.value = mergeIncomingNotifications(base, []);
  setTimeout(() => {
    isRefreshing.value = false;
  }, 420);
}

// ---- 页签与清除未读 ----

function switchTab(tab: MessagesTabKey) {
  activeTab.value = tab;
  closeSwipe();
}

function openClearConfirm() {
  if (unreadCount.value === 0) {
    return;
  }
  isClearConfirmVisible.value = true;
}

function closeClearConfirm() {
  isClearConfirmVisible.value = false;
}

function handleClearAllUnread() {
  applyMessages(markAllRead(messages.value));
  isClearConfirmVisible.value = false;
  uni.showToast({ title: "未读已清除", icon: "none" });
}

// ---- 左滑操作 ----

function rpx(value: number): number {
  return uni.upx2px(value);
}

const SWIPE_ACTIONS_WIDTH_RPX = 372;

function isCellSwiping(id: string): boolean {
  return swipeOpenId.value === id || swipeDraggingId.value === id;
}

function cardTransformStyle(id: string): string {
  const isOpen = swipeOpenId.value === id;
  const isDragging = swipeDraggingId.value === id;
  if (!isOpen && !isDragging) {
    return "";
  }
  const offset = isDragging ? swipeDragX.value : -rpx(SWIPE_ACTIONS_WIDTH_RPX);
  return `transform: translateX(${offset}px);`;
}

function closeSwipe() {
  swipeOpenId.value = "";
  swipeDraggingId.value = "";
  swipeDragX.value = 0;
}

function onCardTouchStart(id: string, event: TouchEvent) {
  const touch = event.touches?.[0];
  if (!touch) {
    return;
  }
  touchStartX = touch.clientX;
  touchStartY = touch.clientY;
  touchDirection = "none";
  if (swipeOpenId.value && swipeOpenId.value !== id) {
    closeSwipe();
  }
}

function onCardTouchMove(id: string, event: TouchEvent) {
  const touch = event.touches?.[0];
  if (!touch || menuTarget.value) {
    return;
  }
  const deltaX = touch.clientX - touchStartX;
  const deltaY = touch.clientY - touchStartY;

  if (touchDirection === "none") {
    if (Math.abs(deltaX) < 8 && Math.abs(deltaY) < 8) {
      return;
    }
    touchDirection = Math.abs(deltaX) > Math.abs(deltaY) ? "horizontal" : "vertical";
  }
  if (touchDirection !== "horizontal") {
    return;
  }

  const baseOffset = swipeOpenId.value === id ? -rpx(SWIPE_ACTIONS_WIDTH_RPX) : 0;
  const next = Math.min(0, Math.max(-rpx(SWIPE_ACTIONS_WIDTH_RPX), baseOffset + deltaX));
  swipeDraggingId.value = id;
  swipeDragX.value = next;
}

function onCardTouchEnd(id: string) {
  if (swipeDraggingId.value !== id) {
    return;
  }
  const threshold = -rpx(SWIPE_ACTIONS_WIDTH_RPX) * 0.42;
  swipeOpenId.value = swipeDragX.value <= threshold ? id : "";
  swipeDraggingId.value = "";
  swipeDragX.value = 0;
  touchDirection = "none";
}

function handleSwipeRead(msg: NotificationView) {
  applyMessages(msg.is_read ? markUnread(messages.value, msg.id) : markRead(messages.value, msg.id));
  closeSwipe();
}

function handleSwipePin(msg: NotificationView) {
  applyMessages(togglePinned(messages.value, msg.id));
  closeSwipe();
}

function handleSwipeDone(msg: NotificationView) {
  applyMessages(dismissNotification(messages.value, msg.id));
  closeSwipe();
  uni.showToast({ title: "已完成，不再展示", icon: "none" });
}

// ---- 点按与长按菜单 ----

function handleCardTap(msg: NotificationView) {
  if (swipeOpenId.value) {
    closeSwipe();
    return;
  }
  if (!msg.is_read) {
    applyMessages(markRead(messages.value, msg.id));
  }
}

function openActionMenu(msg: NotificationView) {
  if (swipeOpenId.value || swipeDraggingId.value) {
    closeSwipe();
    return;
  }
  isLabelPickerOpen.value = false;
  uni
    .createSelectorQuery()
    .select(`#msg-card-${msg.id}`)
    .boundingClientRect((rect) => {
      const box = Array.isArray(rect) ? rect[0] : rect;
      if (!box || box.width === undefined) {
        return;
      }
      ghostRect.value = {
        top: box.top ?? 0,
        left: box.left ?? 0,
        width: box.width ?? 0,
        height: box.height ?? 0,
      };
      menuTarget.value = msg;
    })
    .exec();
}

function closeActionMenu() {
  menuTarget.value = null;
  ghostRect.value = null;
  isLabelPickerOpen.value = false;
}

function handleMenuPin() {
  if (!menuTarget.value) {
    return;
  }
  applyMessages(togglePinned(messages.value, menuTarget.value.id));
  closeActionMenu();
}

function handleMenuToggleRead() {
  if (!menuTarget.value) {
    return;
  }
  const target = menuTarget.value;
  applyMessages(
    target.is_read ? markUnread(messages.value, target.id) : markRead(messages.value, target.id),
  );
  closeActionMenu();
}

function toggleLabelPicker() {
  isLabelPickerOpen.value = !isLabelPickerOpen.value;
}

function handleMenuLabel(labelKey: NotificationLabelKey) {
  if (!menuTarget.value) {
    return;
  }
  applyMessages(setLabel(messages.value, menuTarget.value.id, labelKey));
  closeActionMenu();
}

function handleMenuDone() {
  if (!menuTarget.value) {
    return;
  }
  applyMessages(dismissNotification(messages.value, menuTarget.value.id));
  closeActionMenu();
  uni.showToast({ title: "已完成，不再展示", icon: "none" });
}

// ---- 生命周期 ----

onShow(async () => {
  const accessToken = await resolveAccessToken();
  if (!accessToken) {
    return;
  }
  loadInitialMessages();
  openChannel();
  nowTick.value = Date.now();
  if (!clockTimer) {
    clockTimer = setInterval(() => {
      nowTick.value = Date.now();
    }, 30_000);
  }
});

onHide(() => {
  closeChannel();
  closeActionMenu();
  closeSwipe();
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
});

onUnload(() => {
  closeChannel();
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
});
</script>

<style scoped>
.messages-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background: #f7fbef;
  color: #151a20;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.messages-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 154rpx);
  display: flex;
  flex-direction: column;
  transition: filter 0.28s ease, transform 0.28s ease;
}

/* 长按 / 确认弹层出现时，背景重度虚化下沉 */
.messages-inner.is-dimmed {
  filter: blur(16rpx) saturate(0.86);
  transform: scale(0.985);
}

.messages-fixed {
  flex: 0 0 auto;
}

.messages-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 24rpx;
}

.messages-body {
  padding-bottom: 24rpx;
}

.page-title {
  margin-bottom: 28rpx;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.page-title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.page-title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
  transform: scale(1.4);
  transform-origin: center;
}

.page-title-subrow {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.page-title-subtitle {
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.live-status {
  display: flex;
  align-items: center;
  gap: 8rpx;
  border-radius: 999rpx;
  padding: 4rpx 14rpx;
  background: rgba(255, 255, 255, 0.72);
  border: 2rpx solid rgba(203, 228, 197, 0.8);
}

.live-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #9aa4ad;
}

.live-text {
  color: #6b7280;
  font-size: 20rpx;
  font-weight: 800;
  line-height: 1;
}

.live-connected .live-dot {
  background: #35a04a;
  box-shadow: 0 0 0 5rpx rgba(53, 160, 74, 0.16);
}

.live-connected .live-text {
  color: #2c8136;
}

.live-connecting .live-dot {
  background: #e0a53f;
  animation: livePulse 1.1s ease-in-out infinite;
}

.live-connecting .live-text {
  color: #a9720e;
}

@keyframes livePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(224, 165, 63, 0.32);
  }

  50% {
    box-shadow: 0 0 0 7rpx rgba(224, 165, 63, 0.12);
  }
}

.tab-row {
  display: flex;
  align-items: center;
}

.segment {
  display: flex;
  align-items: center;
  gap: 6rpx;
  border: 2rpx solid rgba(203, 228, 197, 0.85);
  border-radius: 999rpx;
  padding: 6rpx;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 10rpx 26rpx rgba(39, 76, 42, 0.07);
}

.segment-item {
  min-width: 168rpx;
  height: 66rpx;
  margin: 0;
  padding: 0 30rpx;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  background: transparent;
  color: #5a6470;
  font-size: 27rpx;
  font-weight: 800;
  line-height: 62rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  transition: background 0.22s ease, color 0.22s ease;
}

.segment-item::after {
  border: 0;
}

.segment-item.is-active {
  border-color: rgba(63, 138, 70, 0.55);
  background: #ffffff;
  color: #256e2e;
  box-shadow: 0 8rpx 18rpx rgba(45, 114, 51, 0.14);
}

.segment-badge {
  min-width: 34rpx;
  height: 34rpx;
  box-sizing: border-box;
  border-radius: 999rpx;
  padding: 0 8rpx;
  background: #e2574c;
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 34rpx;
  text-align: center;
}

/* “清除全部未读”栏：切到未读页时展开滑入 */
.clear-bar {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transform: translateY(-8rpx);
  transition: max-height 0.3s ease, opacity 0.26s ease, transform 0.26s ease;
}

.clear-bar.is-visible {
  max-height: 120rpx;
  opacity: 1;
  transform: translateY(0);
}

.clear-bar-button {
  width: 100%;
  height: 76rpx;
  box-sizing: border-box;
  margin: 20rpx 0 0;
  padding: 0 26rpx;
  border: 2rpx dashed rgba(194, 86, 74, 0.4);
  border-radius: 22rpx;
  background: rgba(255, 251, 248, 0.92);
  display: flex;
  align-items: center;
  gap: 14rpx;
  box-shadow: 0 10rpx 24rpx rgba(120, 53, 45, 0.06);
}

.clear-bar-button::after {
  border: 0;
}

.clear-bar-hover {
  background: rgba(253, 240, 236, 0.96);
}

.clear-bar-icon {
  width: 34rpx;
  height: 34rpx;
  filter: brightness(0) saturate(100%) invert(41%) sepia(31%) saturate(1497%) hue-rotate(324deg)
    brightness(92%) contrast(88%);
}

.clear-bar-text {
  color: #bb4a3e;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 1;
}

.clear-bar-count {
  margin-left: auto;
  color: #a5776f;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1;
}

/* ---- 消息列表 ---- */

.message-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.swipe-cell {
  position: relative;
  border-radius: 28rpx;
  animation: cardIn 0.26s ease both;
}

.swipe-cell.is-swiping {
  overflow: hidden;
}

.swipe-actions {
  position: absolute;
  inset: 0 0 0 auto;
  width: 372rpx;
  border-radius: 28rpx;
  overflow: hidden;
  display: flex;
}

.swipe-action {
  flex: 1;
  height: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.swipe-action::after {
  border: 0;
}

.swipe-action-icon {
  font-size: 34rpx;
  line-height: 1;
}

.swipe-action-text {
  font-size: 22rpx;
  font-weight: 900;
  line-height: 1;
}

.action-read {
  background: #6f9a54;
}

.action-pin {
  background: #d9a441;
}

.action-done {
  background: #2f7d3a;
}

.message-card {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  min-height: 150rpx;
  border: 2rpx solid rgba(197, 230, 193, 0.78);
  border-radius: 28rpx;
  padding: 26rpx 26rpx 26rpx 24rpx;
  background: #fbfdf8;
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  overflow: hidden;
  transition: transform 0.26s cubic-bezier(0.22, 1, 0.36, 1);
}

.message-card.is-dragging {
  transition: none;
}

.message-card.is-unread {
  border-color: rgba(226, 127, 111, 0.5);
  background: #fffdfa;
}

.message-card.is-pinned {
  border-color: rgba(217, 164, 65, 0.55);
}

@keyframes cardIn {
  0% {
    opacity: 0;
    transform: translateY(14rpx);
  }

  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-avatar {
  width: 92rpx;
  height: 92rpx;
  flex: 0 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-green {
  background: #e6f3dd;
}

.avatar-amber {
  background: #fdf3e0;
}

.avatar-violet {
  background: #efeaf8;
}

.avatar-leaf {
  background: #eaf3e2;
}

.avatar-sky {
  background: linear-gradient(160deg, #4f9ad2 0%, #71b3e4 100%);
}

.avatar-rose {
  background: #fdecec;
}

.card-avatar-icon {
  width: 52rpx;
  height: 52rpx;
}

.avatar-icon-task {
  filter: brightness(0) saturate(100%) invert(34%) sepia(18%) saturate(1068%) hue-rotate(51deg)
    brightness(92%) contrast(86%);
}

.avatar-icon-supply {
  filter: brightness(0) saturate(100%) invert(34%) sepia(18%) saturate(1068%) hue-rotate(51deg)
    brightness(92%) contrast(86%);
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.card-source {
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  color: #16211a;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-badge,
.card-label {
  flex: 0 0 auto;
  border-radius: 12rpx;
  padding: 5rpx 12rpx;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 1.1;
}

.badge-green {
  background: #e7f6df;
  color: #238033;
}

.badge-amber {
  background: #fdf3dc;
  color: #a9720e;
}

.badge-violet {
  background: #eee8ff;
  color: #684ce5;
}

.badge-sky {
  background: #e6f0ff;
  color: #2d72d9;
}

.badge-rose {
  background: #ffe7eb;
  color: #d73546;
}

.badge-leaf {
  background: #e9f4de;
  color: #3f7d2e;
}

.label-rose {
  background: #ffe7eb;
  color: #d73546;
}

.label-amber {
  background: #fdf3dc;
  color: #a9720e;
}

.label-green {
  background: #e7f6df;
  color: #238033;
}

.card-time {
  margin-left: auto;
  flex: 0 0 auto;
  color: #9aa4ad;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
}

.card-content-row {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.card-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #5b6570;
  font-size: 25rpx;
  font-weight: 600;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-content-full {
  white-space: normal;
}

.unread-dot {
  width: 16rpx;
  height: 16rpx;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #e2574c;
  box-shadow: 0 0 0 5rpx rgba(226, 87, 76, 0.14);
}

/* 置顶：右上角折角书签 */
.pin-fold {
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 44rpx 44rpx 0;
  border-color: transparent #e3bd72 transparent transparent;
}

.list-footer {
  margin-top: 26rpx;
  min-height: 48rpx;
  color: #8a949e;
  font-size: 24rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.footer-paw {
  font-size: 22rpx;
  opacity: 0.55;
}

/* ---- 空状态 ---- */

.empty-card {
  box-sizing: border-box;
  border: 2rpx solid rgba(197, 230, 193, 0.78);
  border-radius: 32rpx;
  margin-top: 8rpx;
  padding: 64rpx 44rpx 58rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-illustration {
  width: 360rpx;
  height: 300rpx;
}

.empty-title {
  margin-top: 26rpx;
  color: #2f7d2e;
  font-size: 36rpx;
  font-weight: 900;
  letter-spacing: 2rpx;
}

.empty-desc {
  margin-top: 16rpx;
  max-width: 460rpx;
  color: #6b7280;
  font-size: 25rpx;
  font-weight: 600;
  line-height: 1.5;
}

/* ---- 长按弹层 ---- */

.press-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(36, 52, 38, 0.34);
  backdrop-filter: blur(24rpx);
  animation: overlayIn 0.22s ease both;
}

@keyframes overlayIn {
  0% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}

.press-ghost {
  position: fixed;
  z-index: 41;
}

.message-card.is-elevated {
  animation: elevate 0.24s cubic-bezier(0.34, 1.4, 0.5, 1) both;
  box-shadow: 0 30rpx 68rpx rgba(23, 46, 27, 0.32);
}

@keyframes elevate {
  0% {
    transform: scale(1);
  }

  100% {
    transform: scale(1.025);
  }
}

.press-menu {
  position: fixed;
  z-index: 42;
  box-sizing: border-box;
  border: 2rpx solid rgba(222, 236, 218, 0.9);
  border-radius: 30rpx;
  padding: 10rpx 8rpx;
  background: #ffffff;
  box-shadow: 0 26rpx 62rpx rgba(23, 46, 27, 0.26);
  animation: menuPop 0.24s cubic-bezier(0.34, 1.35, 0.5, 1) both;
  transform-origin: top right;
}

@keyframes menuPop {
  0% {
    opacity: 0;
    transform: scale(0.86) translateY(-8rpx);
  }

  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.menu-item {
  width: 100%;
  height: 92rpx;
  box-sizing: border-box;
  margin: 0;
  padding: 0 26rpx;
  border: 0;
  border-radius: 22rpx;
  background: transparent;
  color: #22301f;
  font-size: 28rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.menu-item::after {
  border: 0;
}

.menu-item-hover {
  background: rgba(233, 244, 222, 0.75);
}

.menu-item-text {
  flex: 1;
}

.menu-item-icon {
  flex: 0 0 auto;
  color: #557f5f;
  font-size: 30rpx;
  font-weight: 700;
}

.menu-item.is-expanded {
  background: rgba(240, 247, 233, 0.85);
}

.label-picker {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 0 22rpx;
  transition: max-height 0.24s ease, opacity 0.2s ease, padding 0.24s ease;
}

.label-picker.is-open {
  max-height: 96rpx;
  opacity: 1;
  padding: 12rpx 22rpx 16rpx;
}

.label-chip {
  flex: 1;
  height: 56rpx;
  margin: 0;
  padding: 0;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 52rpx;
}

.label-chip::after {
  border: 0;
}

.label-chip.is-selected {
  border-color: currentColor;
}

.menu-divider {
  height: 2rpx;
  margin: 8rpx 22rpx;
  background: rgba(214, 228, 208, 0.9);
}

.menu-item-done {
  color: #256e2e;
}

.menu-item-done .menu-item-icon {
  color: #2c8136;
}

/* ---- 清除未读确认弹层 ---- */

.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(36, 52, 38, 0.4);
  backdrop-filter: blur(20rpx);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: overlayIn 0.22s ease both;
}

.confirm-card {
  width: 570rpx;
  box-sizing: border-box;
  border: 2rpx solid rgba(231, 240, 226, 0.92);
  border-radius: 40rpx;
  padding: 46rpx 40rpx 36rpx;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 30rpx 74rpx rgba(23, 46, 27, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  animation: menuPop 0.26s cubic-bezier(0.34, 1.35, 0.5, 1) both;
  transform-origin: center;
}

.confirm-icon-ring {
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
  background: #fdecec;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-icon {
  width: 52rpx;
  height: 52rpx;
  filter: brightness(0) saturate(100%) invert(41%) sepia(31%) saturate(1497%) hue-rotate(324deg)
    brightness(92%) contrast(88%);
}

.confirm-title {
  margin-top: 26rpx;
  color: #1c2a20;
  font-size: 36rpx;
  font-weight: 900;
  letter-spacing: 2rpx;
}

.confirm-desc {
  margin-top: 18rpx;
  color: #67707b;
  font-size: 25rpx;
  font-weight: 600;
  line-height: 1.55;
}

.confirm-actions {
  width: 100%;
  margin-top: 40rpx;
  display: flex;
  gap: 20rpx;
}

.confirm-button {
  flex: 1;
  height: 84rpx;
  margin: 0;
  padding: 0;
  border-radius: 24rpx;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 84rpx;
}

.confirm-button::after {
  border: 0;
}

.confirm-button-hover {
  transform: translateY(2rpx);
  opacity: 0.92;
}

.confirm-cancel {
  border: 2rpx solid rgba(191, 217, 184, 0.85);
  background: rgba(255, 255, 255, 0.85);
  color: #4c5a50;
}

.confirm-primary {
  border: 0;
  background: linear-gradient(90deg, #338a32 0%, #28772d 100%);
  color: #ffffff;
  box-shadow: 0 14rpx 28rpx rgba(45, 122, 45, 0.22);
}
</style>
