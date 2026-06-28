<template>
  <view class="loading-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />

    <view class="content">
      <view class="brand-block">
        <image class="association-logo" :src="loadingLogo" mode="aspectFit" />
        <text class="app-title">猫协地图</text>
        <text class="app-subtitle">探索校园 · 守护猫咪</text>
        <view class="system-name">
          <image class="wheat-icon wheat-icon-left" :src="wheatRightIcon" mode="aspectFit" />
          <text>校园猫咪任务协作系统</text>
          <image class="wheat-icon wheat-icon-right" :src="wheatLeftIcon" mode="aspectFit" />
        </view>
      </view>

      <view class="loader-block">
        <view class="paw-loader" aria-label="加载中">
          <image class="loading-paw paw-one" :src="pawIcon" mode="aspectFit" />
          <image class="loading-paw paw-two" :src="pawIcon" mode="aspectFit" />
          <image class="loading-paw paw-three" :src="pawIcon" mode="aspectFit" />
        </view>
        <view class="message-shell">
          <text :key="activeMessage" class="loading-message">
            {{ activeMessage }}
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import {
  LOGIN_ROUTE,
  resolveStartupRoute,
  type StartupRoute,
} from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import loadingBackground from "../../../素材/加载页素材/加载页背景.jpg";
import loadingLogo from "../../../素材/加载页素材/加载页会徽.png";
import wheatLeftIcon from "../../../素材/加载页素材/麦穗1.svg";
import wheatRightIcon from "../../../素材/加载页素材/麦穗2.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";

const LOADING_MESSAGES = [
  "正在寻找校园里的猫猫...",
  "正在加载猫咪地图...",
  "猫猫正在带路中...",
] as const;

const MESSAGE_INTERVAL_MS = 2600;
const MIN_LOADING_DURATION_MS = 1200;

const userStore = useUserStore();
const messageIndex = ref(0);
let messageTimer: ReturnType<typeof setInterval> | undefined;

const activeMessage = computed(() => LOADING_MESSAGES[messageIndex.value]);

function waitForMinimumLoadingTime(): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, MIN_LOADING_DURATION_MS);
  });
}

function navigateTo(route: StartupRoute): Promise<void> {
  return new Promise((resolve) => {
    uni.reLaunch({
      url: route,
      complete: () => resolve(),
    });
  });
}

async function beginStartup() {
  const [route] = await Promise.all([
    resolveStartupRoute(userStore),
    waitForMinimumLoadingTime(),
  ]);

  await navigateTo(route);
}

onMounted(() => {
  messageTimer = setInterval(() => {
    messageIndex.value = (messageIndex.value + 1) % LOADING_MESSAGES.length;
  }, MESSAGE_INTERVAL_MS);

  void beginStartup().catch(() => {
    userStore.clearSession();
    void navigateTo(LOGIN_ROUTE);
  });
});

onUnmounted(() => {
  if (messageTimer) {
    clearInterval(messageTimer);
  }
});
</script>

<style scoped>
.loading-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #f7fbef;
  font-family: "Songti SC", "STSong", "SimSun", serif;
}

.page-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.content {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  box-sizing: border-box;
  padding: 248rpx 44rpx 214rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
}

.brand-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.association-logo {
  width: 516rpx;
  height: 516rpx;
  filter: drop-shadow(0 24rpx 38rpx rgba(61, 110, 47, 0.22));
}

.app-title {
  margin-top: 64rpx;
  color: #276f2e;
  font-size: 96rpx;
  font-weight: 900;
  line-height: 1;
  letter-spacing: 7rpx;
  text-shadow: 0 8rpx 18rpx rgba(39, 111, 46, 0.16);
}

.app-subtitle {
  margin-top: 42rpx;
  color: #6b7570;
  font-size: 42rpx;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 4rpx;
}

.system-name {
  margin-top: 54rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  color: #6f7b73;
  font-size: 29rpx;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 2rpx;
}

.wheat-icon {
  width: 32rpx;
  height: 32rpx;
  opacity: 0.68;
  flex: 0 0 auto;
}

.wheat-icon-left {
  transform: rotate(-24deg);
}

.wheat-icon-right {
  transform: rotate(24deg);
}

.loader-block {
  width: 100%;
  min-height: 164rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.paw-loader {
  width: 214rpx;
  height: 70rpx;
  box-sizing: border-box;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 14rpx 30rpx rgba(73, 117, 54, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.loading-paw {
  width: 40rpx;
  height: 40rpx;
  opacity: 0.32;
  transform: scale(0.82);
  animation: pawPulse 1.55s ease-in-out infinite;
}

.paw-two {
  animation-delay: 0.22s;
}

.paw-three {
  animation-delay: 0.44s;
}

.message-shell {
  height: 48rpx;
  margin-top: 38rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.loading-message {
  display: block;
  font-size: 31rpx;
  font-weight: 800;
  line-height: 48rpx;
  letter-spacing: 2rpx;
  text-align: center;
  color: #4a7c3d;
  background-image: linear-gradient(90deg, #9fb894 0%, #2f7f33 48%, #b8cfaa 100%);
  background-size: 220% 100%;
  background-position: 100% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: messageFade 2.52s ease-in-out both;
}

@keyframes pawPulse {
  0%,
  100% {
    opacity: 0.26;
    transform: translateY(0) scale(0.82);
  }

  45% {
    opacity: 1;
    transform: translateY(-8rpx) scale(1);
  }
}

@keyframes messageFade {
  0% {
    opacity: 0;
    transform: translateY(14rpx);
    background-position: 100% 0;
  }

  16% {
    opacity: 1;
    transform: translateY(0);
  }

  72% {
    opacity: 1;
    transform: translateY(0);
    background-position: 0 0;
  }

  100% {
    opacity: 0;
    transform: translateY(-10rpx);
    background-position: 0 0;
  }
}
</style>
