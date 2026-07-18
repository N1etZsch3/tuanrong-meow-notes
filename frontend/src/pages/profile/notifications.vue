<template>
  <view class="notify-page">
    <image class="page-bg" :src="pageBackground" mode="aspectFill" />
    <scroll-view class="notify-scroll" scroll-y enhanced :show-scrollbar="false">
      <view class="notify-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="nav-copy">
            <text class="nav-title">消息通知</text>
            <text class="nav-subtitle">按类型管理你想接收的通知</text>
          </view>
        </view>

        <view class="settings-group">
          <view
            v-for="(item, index) in CHANNEL_ITEMS"
            :key="item.key"
            class="settings-row"
          >
            <view class="row-copy">
              <text class="row-title">{{ item.title }}</text>
              <text class="row-desc">{{ item.desc }}</text>
            </view>
            <switch
              :checked="settings[item.key]"
              color="#2f8037"
              :disabled="isSaving"
              @change="onToggle(item.key, $event)"
            />
            <view v-if="index < CHANNEL_ITEMS.length - 1" class="row-divider" />
          </view>
        </view>

        <text class="notify-hint">
          关闭某类通知后，将不再向你推送该类新消息；已有消息记录仍会保留。
        </text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import {
  getNotificationSettings,
  updateNotificationSettings,
  type NotificationSettingsDto,
} from "@/api/notifications";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import pageBackground from "../../../素材/加载页素材/背景.jpg";

type SettingKey = keyof NotificationSettingsDto;

const CHANNEL_ITEMS: Array<{ key: SettingKey; title: string; desc: string }> = [
  { key: "task_enabled", title: "任务系统", desc: "新任务发布、指派与状态变更" },
  { key: "feeding_enabled", title: "喂食提醒", desc: "今日投喂打卡提醒" },
  { key: "medicine_enabled", title: "药品管理", desc: "库存变动与用药提醒" },
  { key: "supply_enabled", title: "物资通知", desc: "物资补货与领取提醒" },
  { key: "member_enabled", title: "成员通知", desc: "审核结果与成员相关动态" },
  { key: "cat_enabled", title: "猫咪健康", desc: "猫咪健康异常提醒" },
  { key: "announcement_enabled", title: "系统公告", desc: "值班表与协会公告" },
];

const userStore = useUserStore();
const isSaving = ref(false);
const settings = reactive<NotificationSettingsDto>({
  task_enabled: true,
  feeding_enabled: true,
  medicine_enabled: true,
  supply_enabled: true,
  member_enabled: true,
  cat_enabled: true,
  announcement_enabled: true,
});

function applySettings(next: NotificationSettingsDto) {
  for (const item of CHANNEL_ITEMS) {
    settings[item.key] = next[item.key];
  }
}

async function loadSettings() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }
  try {
    applySettings(await getNotificationSettings(accessToken));
  } catch (error) {
    const message = error instanceof Error ? error.message : "通知设置加载失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

async function onToggle(key: SettingKey, event: any) {
  const nextValue = Boolean(event?.detail?.value);
  const previous = settings[key];
  settings[key] = nextValue;
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }
  isSaving.value = true;
  try {
    applySettings(await updateNotificationSettings(accessToken, { [key]: nextValue }));
  } catch (error) {
    settings[key] = previous;
    const message = error instanceof Error ? error.message : "保存失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSaving.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  void loadSettings();
});
</script>

<style scoped>
.notify-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.notify-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.notify-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
  margin-bottom: 40rpx;
}

.back-button {
  width: 68rpx;
  height: 68rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #2f8037;
  font-size: 58rpx;
  line-height: 58rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.12);
}

.back-button::after {
  border: 0;
}

.nav-copy {
  min-width: 0;
}

.nav-title,
.nav-subtitle {
  display: block;
}

.nav-title {
  color: #171b22;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #656d78;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.settings-group {
  overflow: hidden;
  border: 1rpx solid rgba(207, 218, 208, 0.72);
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8rpx 24rpx rgba(42, 63, 43, 0.07);
}

.settings-row {
  position: relative;
  box-sizing: border-box;
  min-height: 104rpx;
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.row-copy {
  min-width: 0;
  flex: 1;
}

.row-title,
.row-desc {
  display: block;
}

.row-title {
  color: #22272f;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.2;
}

.row-desc {
  margin-top: 8rpx;
  color: #6f7780;
  font-size: 23rpx;
  line-height: 1.3;
}

.row-divider {
  position: absolute;
  left: 24rpx;
  right: 0;
  bottom: 0;
  height: 1rpx;
  background: rgba(210, 218, 213, 0.74);
}

.notify-hint {
  display: block;
  margin: 22rpx 18rpx 0;
  color: #7a828c;
  font-size: 23rpx;
  line-height: 1.6;
}
</style>
