<template>
  <view class="loading-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />

    <view class="content">
      <view class="brand-scene">
        <image class="cat-illustration" :src="catIllustration" mode="aspectFit" />
        <image class="app-wordmark" :src="appWordmark" mode="aspectFill" />
        <text class="app-tagline">记录每一次温暖的相遇</text>

        <view
          class="progress-section"
          role="progressbar"
          aria-label="应用启动进度"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-valuenow="loadingProgress"
        >
          <view class="progress-track">
            <view class="progress-fill" :style="progressFillStyle">
              <view class="progress-highlight" />
            </view>
          </view>

          <view class="progress-copy">
            <image class="progress-paw" :src="pawIcon" mode="aspectFit" />
            <view class="progress-text">
              <text>{{ progressMessage }}</text>
              <text class="progress-percent">{{ loadingProgress }}%</text>
            </view>
          </view>
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
import {
  advanceStartupProgress,
  STARTUP_PROGRESS_INITIAL,
} from "./loading-page";

import loadingBackground from "../../../素材/加载页素材/背景.jpg";
import catIllustration from "../../../素材/加载页素材/团绒猫.png";
import appWordmark from "../../../素材/加载页素材/团绒喵记本字标.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";

const MIN_LOADING_DURATION_MS = 1200;
const PROGRESS_INTERVAL_MS = 80;
const PROGRESS_COMPLETION_HOLD_MS = 180;

const userStore = useUserStore();
const loadingProgress = ref(STARTUP_PROGRESS_INITIAL);
let progressTimer: ReturnType<typeof setInterval> | undefined;

const progressFillStyle = computed(() => ({
  width: `${loadingProgress.value}%`,
}));

const progressMessage = computed(() =>
  loadingProgress.value >= 100 ? "加载完成" : "正在加载中...",
);

function wait(durationMs: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, durationMs);
  });
}

function waitForMinimumLoadingTime(): Promise<void> {
  return wait(MIN_LOADING_DURATION_MS);
}

function navigateTo(route: StartupRoute): Promise<void> {
  return new Promise((resolve) => {
    uni.reLaunch({
      url: route,
      complete: () => resolve(),
    });
  });
}

function stopProgressAnimation() {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = undefined;
  }
}

function startProgressAnimation() {
  stopProgressAnimation();
  loadingProgress.value = STARTUP_PROGRESS_INITIAL;
  progressTimer = setInterval(() => {
    loadingProgress.value = advanceStartupProgress(loadingProgress.value);
  }, PROGRESS_INTERVAL_MS);
}

async function completeLoadingProgress() {
  stopProgressAnimation();
  loadingProgress.value = 100;
  await wait(PROGRESS_COMPLETION_HOLD_MS);
}

async function beginStartup() {
  const [route] = await Promise.all([
    resolveStartupRoute(userStore),
    waitForMinimumLoadingTime(),
  ]);

  await completeLoadingProgress();
  await navigateTo(route);
}

onMounted(() => {
  startProgressAnimation();

  void beginStartup().catch(async () => {
    userStore.clearSession();
    await completeLoadingProgress();
    await navigateTo(LOGIN_ROUTE);
  });
});

onUnmounted(() => {
  stopProgressAnimation();
});
</script>

<style scoped>
.loading-page {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background: #fbfdf5;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.content {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 100vh;
  box-sizing: border-box;
  padding: max(44rpx, env(safe-area-inset-top)) 38rpx
    max(64rpx, env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-scene {
  width: 100%;
  margin-top: -38rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cat-illustration {
  width: 360rpx;
  height: 310rpx;
  flex: 0 0 auto;
  filter: drop-shadow(0 12rpx 18rpx rgba(122, 154, 75, 0.1));
  animation: catFloat 3.2s ease-in-out infinite;
}

.app-wordmark {
  width: 460rpx;
  height: 110rpx;
  margin-top: 24rpx;
  flex: 0 0 auto;
}

.app-tagline {
  margin-top: -8rpx;
  color: #8a9683;
  font-size: 26rpx;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 2rpx;
  text-align: center;
}

.progress-section {
  width: 310rpx;
  margin-top: 50rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.progress-track {
  position: relative;
  width: 270rpx;
  height: 14rpx;
  overflow: hidden;
  border: 2rpx solid rgba(151, 174, 126, 0.12);
  border-radius: 999rpx;
  background: rgba(220, 225, 210, 0.72);
  box-shadow: inset 0 2rpx 5rpx rgba(109, 130, 88, 0.12);
}

.progress-fill {
  position: relative;
  height: 100%;
  overflow: hidden;
  border-radius: inherit;
  background: linear-gradient(90deg, #a8ca71 0%, #8eba59 72%, #83ad4e 100%);
  box-shadow: 0 2rpx 10rpx rgba(117, 163, 67, 0.2);
  transition: width 180ms ease-out;
}

.progress-highlight {
  position: absolute;
  top: 2rpx;
  right: 8rpx;
  left: 8rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.3);
}

.progress-copy {
  position: relative;
  width: 100%;
  min-height: 44rpx;
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-paw {
  position: absolute;
  left: 0;
  width: 40rpx;
  height: 40rpx;
  opacity: 0.16;
  transform: rotate(-15deg);
}

.progress-text {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10rpx;
  color: #9aa58f;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.5;
  letter-spacing: 1rpx;
  text-align: center;
}

.progress-percent {
  min-width: 58rpx;
  color: #84aa58;
  font-variant-numeric: tabular-nums;
  text-align: left;
}

@keyframes catFloat {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-8rpx);
  }
}

@media screen and (max-height: 680px) {
  .brand-scene {
    margin-top: -28rpx;
    transform: scale(0.92);
  }
}
</style>
