<template>
  <view class="detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">消息详情</text>
            <text class="nav-subtitle">查看通知全文与关联动态</text>
          </view>
        </view>

        <view v-if="!message" class="state-box">
          <image class="state-illustration" :src="emptyMessagesIllustration" mode="aspectFit" />
          <text class="state-title">消息不存在或已被清理</text>
          <text class="state-copy">这条通知可能已完成归档，返回喵息看看其他动态吧。</text>
        </view>

        <view v-else class="detail-content">
          <view class="channel-row">
            <view class="channel-avatar" :class="`avatar-${channel.tone}`">
              <image
                class="channel-avatar-icon"
                :class="`avatar-icon-${channel.icon_key}`"
                :src="channelIcon"
                mode="aspectFit"
              />
            </view>
            <view class="channel-main">
              <view class="channel-title-row">
                <text class="channel-title">{{ channel.title }}</text>
                <text class="channel-badge" :class="`badge-${channel.tone}`">
                  {{ channel.badge }}
                </text>
              </view>
              <text class="channel-time">{{ fullTime }}</text>
            </view>
            <text
              v-if="label"
              class="channel-label"
              :class="`label-${label.tone}`"
            >
              {{ label.text }}
            </text>
          </view>

          <view class="hairline" />

          <view class="body-section">
            <text class="message-title">{{ message.title }}</text>
            <text class="message-content">{{ message.content }}</text>
          </view>

          <view class="hairline" />

          <view class="meta-section">
            <view class="meta-line">
              <text class="meta-label">状态</text>
              <text class="meta-value" :class="{ 'meta-unread': !message.is_read }">
                {{ message.is_read ? "已读" : "未读" }}
              </text>
            </view>
            <view class="meta-line">
              <text class="meta-label">接收时间</text>
              <text class="meta-value">{{ fullTime }}</text>
            </view>
            <view class="meta-line">
              <text class="meta-label">置顶</text>
              <text class="meta-value">{{ message.is_pinned ? "已置顶" : "未置顶" }}</text>
            </view>
            <view class="meta-line">
              <text class="meta-label">消息编号</text>
              <text class="meta-value meta-mono">{{ message.id }}</text>
            </view>
          </view>

          <template v-if="relatedTarget">
            <view class="hairline" />

            <view class="related-section">
              <text class="related-eyebrow">关联内容</text>
              <button
                class="related-line"
                hover-class="related-line-hover"
                @tap="goRelated"
              >
                <view class="related-main">
                  <text class="related-name">{{ relatedTarget.name }}</text>
                  <text class="related-desc">{{ relatedTarget.desc }}</text>
                </view>
                <text class="related-arrow">›</text>
              </button>
              <text class="related-note">演示环境：跳转后为真实数据页面，仅供浏览。</text>
            </view>
          </template>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import {
  MESSAGES_DETAIL_SNAPSHOT_STORAGE_KEY,
  MESSAGES_LOCAL_STATE_STORAGE_KEY,
  getNotificationLabel,
  indexLocalStates,
  resolveNotificationChannel,
  toNotificationView,
  type NotificationChannelKey,
  type NotificationRelatedType,
  type NotificationView,
  type StoredLocalState,
} from "./messages-page";
import { MOCK_NOTIFICATIONS } from "./mock-notifications";

import loadingBackground from "../../../素材/加载页素材/背景.jpg";
import emptyMessagesIllustration from "../../../素材/svg/缺省页/消息空荡荡的.svg";
import taskChannelIcon from "../../../素材/svg/喵记/任务.svg";
import feedingChannelIcon from "../../../素材/svg/喵息/猫粮盆.svg";
import medicineChannelIcon from "../../../素材/svg/喵息/药品.svg";
import supplyChannelIcon from "../../../素材/svg/喵记/物资仓库.svg";
import memberChannelIcon from "../../../素材/svg/喵息/消息.svg";
import catChannelIcon from "../../../素材/svg/默认/猫咪库.svg";

const CHANNEL_ICONS: Record<NotificationChannelKey, string> = {
  task: taskChannelIcon,
  feeding: feedingChannelIcon,
  medicine: medicineChannelIcon,
  supply: supplyChannelIcon,
  member: memberChannelIcon,
  cat: catChannelIcon,
  announcement: memberChannelIcon,
};

interface RelatedTarget {
  name: string;
  desc: string;
  url: string;
}

/**
 * mock 通知的 related_id 并非生产库真实主键，因此演示阶段统一跳到
 * 对应模块的真实列表页（只读浏览），不携带伪造 id 去请求详情接口。
 */
const RELATED_TARGETS: Partial<Record<NotificationRelatedType, RelatedTarget>> = {
  task: {
    name: "喂食任务",
    desc: "前往任务列表查看进行中的投喂安排",
    url: "/pages/tasks/list",
  },
  supply_point: {
    name: "物资点",
    desc: "前往物资列表查看各点位补给情况",
    url: "/pages/supplies/index",
  },
  medicine: {
    name: "药品管理",
    desc: "前往药品管理查看库存与领用记录",
    url: "/pages/medicines/index",
  },
  cat: {
    name: "猫咪库",
    desc: "前往猫咪库查看猫咪档案与健康记录",
    url: "/pages/cats/index",
  },
};

const message = ref<NotificationView | null>(null);

const channel = computed(() =>
  resolveNotificationChannel(message.value?.notification_type ?? "announcement"),
);
const channelIcon = computed(() => CHANNEL_ICONS[channel.value.icon_key]);
const label = computed(() => getNotificationLabel(message.value?.label_key ?? null));
const relatedTarget = computed(() => {
  const type = message.value?.related_type;
  return type ? RELATED_TARGETS[type] ?? null : null;
});

const fullTime = computed(() => {
  if (!message.value) {
    return "";
  }
  const date = new Date(message.value.created_at);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const pad = (value: number) => (value < 10 ? `0${value}` : `${value}`);
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`;
});

function loadStoredLocalStates() {
  try {
    const raw = uni.getStorageSync(MESSAGES_LOCAL_STATE_STORAGE_KEY) as StoredLocalState[] | "";
    return indexLocalStates(Array.isArray(raw) ? raw : null);
  } catch {
    return {};
  }
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }
  uni.reLaunch({ url: "/pages/messages/index" });
}

function goRelated() {
  if (!relatedTarget.value) {
    return;
  }
  uni.navigateTo({ url: relatedTarget.value.url });
}

function loadSnapshot(id: string): NotificationView | null {
  try {
    const raw = uni.getStorageSync(MESSAGES_DETAIL_SNAPSHOT_STORAGE_KEY) as
      | NotificationView
      | "";
    return raw && typeof raw === "object" && raw.id === id ? raw : null;
  } catch {
    return null;
  }
}

onLoad((query) => {
  const rawId = typeof query?.id === "string" ? query.id : "";
  // 小程序端 onLoad 参数不自动解码，H5 端已解码；对普通 id 双重解码无害。
  let id = rawId;
  try {
    id = decodeURIComponent(rawId);
  } catch {
    id = rawId;
  }
  const snapshot = loadSnapshot(id);
  if (snapshot) {
    // 列表页点按即标记已读，详情始终按已读展示。
    message.value = { ...snapshot, is_read: true };
    return;
  }
  const dto = MOCK_NOTIFICATIONS.find((item) => item.id === id) ?? null;
  if (!dto) {
    message.value = null;
    return;
  }
  const locals = loadStoredLocalStates();
  message.value = toNotificationView({ ...dto, is_read: true }, locals[dto.id]);
});
</script>

<style scoped>
.detail-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
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

.detail-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.detail-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 120rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 2rpx solid rgba(216, 229, 209, 0.9);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  font-size: 44rpx;
  line-height: 66rpx;
  flex: 0 0 auto;
}

.back-button::after,
.related-line::after {
  border: 0;
}

.button-hover {
  opacity: 0.85;
}

.nav-title {
  display: block;
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #526070;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

/* ---- 缺省状态 ---- */

.state-box {
  margin-top: 120rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.state-illustration {
  width: 340rpx;
  height: 280rpx;
}

.state-title {
  margin-top: 24rpx;
  color: #2f7d2e;
  font-size: 34rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 14rpx;
  max-width: 480rpx;
  color: #6b7280;
  font-size: 25rpx;
  font-weight: 600;
  line-height: 1.5;
}

/* ---- 正文：通栏排版，发丝线分区，不做卡片 ---- */

.detail-content {
  margin-top: 44rpx;
}

.hairline {
  height: 2rpx;
  margin: 34rpx 0;
  background: rgba(96, 122, 92, 0.22);
}

.channel-row {
  display: flex;
  align-items: center;
  gap: 22rpx;
}

.channel-avatar {
  width: 96rpx;
  height: 96rpx;
  flex: 0 0 auto;
  border-radius: 26rpx;
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

.channel-avatar-icon {
  width: 54rpx;
  height: 54rpx;
}

.avatar-icon-task,
.avatar-icon-supply {
  filter: brightness(0) saturate(100%) invert(34%) sepia(18%) saturate(1068%) hue-rotate(51deg)
    brightness(92%) contrast(86%);
}

.channel-main {
  flex: 1;
  min-width: 0;
}

.channel-title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.channel-title {
  color: #16211a;
  font-size: 32rpx;
  font-weight: 900;
  line-height: 1.2;
}

.channel-badge,
.channel-label {
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

.channel-time {
  display: block;
  margin-top: 12rpx;
  color: #8a949e;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.2;
}

/* ---- 正文 ---- */

.body-section {
  display: flex;
  flex-direction: column;
}

.message-title {
  color: #111827;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1.35;
}

.message-content {
  margin-top: 22rpx;
  color: #414c58;
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.75;
}

/* ---- 属性区 ---- */

.meta-section {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.meta-line {
  display: flex;
  align-items: baseline;
  gap: 24rpx;
}

.meta-label {
  flex: 0 0 132rpx;
  color: #8a949e;
  font-size: 25rpx;
  font-weight: 700;
}

.meta-value {
  flex: 1;
  min-width: 0;
  color: #2c3844;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.4;
}

.meta-unread {
  color: #d73546;
}

.meta-mono {
  font-weight: 600;
  letter-spacing: 1rpx;
}

/* ---- 关联内容 ---- */

.related-eyebrow {
  display: block;
  color: #8a949e;
  font-size: 25rpx;
  font-weight: 700;
}

.related-line {
  width: 100%;
  box-sizing: border-box;
  margin: 22rpx 0 0;
  padding: 24rpx 0;
  border: 0;
  border-top: 2rpx solid rgba(96, 122, 92, 0.14);
  border-bottom: 2rpx solid rgba(96, 122, 92, 0.14);
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 20rpx;
  text-align: left;
}

.related-line-hover {
  background: rgba(233, 244, 222, 0.5);
}

.related-main {
  flex: 1;
  min-width: 0;
}

.related-name {
  display: block;
  color: #256e2e;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.3;
}

.related-desc {
  display: block;
  margin-top: 10rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.4;
}

.related-arrow {
  flex: 0 0 auto;
  color: #557f5f;
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1;
}

.related-note {
  display: block;
  margin-top: 18rpx;
  color: #9aa4ad;
  font-size: 22rpx;
  font-weight: 600;
  line-height: 1.4;
}
</style>
