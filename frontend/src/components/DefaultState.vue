<template>
  <view class="default-state-page" :class="{ 'with-tab-bar': withTabBar }">
    <image class="default-page-bg" :src="loadingBackground" mode="aspectFill" />

    <view v-if="showBack" class="back-control" @tap="handleBack">
      <text class="back-icon">‹</text>
    </view>

    <view class="default-state-content">
      <view class="state-heading">
        <text class="heading-title">{{ resolvedPreset.eyebrow }}</text>
        <view class="heading-subtitle">
          <text class="leaf">⌞</text>
          <text>校园猫咪任务协作系统</text>
          <text class="leaf">⌝</text>
        </view>
      </view>

      <view class="state-card">
        <view class="sparkle sparkle-one" />
        <view class="sparkle sparkle-two" />
        <image class="state-illustration" :src="resolvedPreset.illustration" mode="aspectFit" />
        <text class="state-title">{{ title || resolvedPreset.title }}</text>
        <text class="state-description">
          {{ description || resolvedPreset.description }}
        </text>

        <button
          v-if="resolvedPrimaryAction"
          class="state-action primary-action"
          hover-class="state-action-hover"
          @tap="emitPrimary"
        >
          <text class="action-icon">{{ resolvedPrimaryAction.icon }}</text>
          <text>{{ resolvedPrimaryAction.label }}</text>
        </button>

        <button
          v-if="resolvedSecondaryAction"
          class="state-action secondary-action"
          hover-class="secondary-action-hover"
          @tap="emitSecondary"
        >
          <text class="secondary-action-icon">{{ resolvedSecondaryAction.icon }}</text>
          <text>{{ resolvedSecondaryAction.label }}</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import {
  getDefaultStatePreset,
  type DefaultStateAction,
  type DefaultStateKey,
} from "./default-state";

import loadingBackground from "../../素材/加载页素材/加载页背景.png";

const ACTION_ICONS: Record<string, string> = {
  back: "‹",
  clock: "◷",
  grid: "▦",
  home: "⌂",
  map: "▰",
  paw: "●",
  pin: "⌖",
  refresh: "↻",
  search: "⌕",
  user: "♙",
  wifi: "≋",
};

const props = withDefaults(
  defineProps<{
    state: DefaultStateKey;
    title?: string;
    description?: string;
    primaryLabel?: string;
    primaryIcon?: string;
    secondaryLabel?: string;
    secondaryIcon?: string;
    showBack?: boolean;
    withTabBar?: boolean;
  }>(),
  {
    showBack: false,
    withTabBar: false,
  },
);

const emit = defineEmits<{
  primary: [];
  secondary: [];
  back: [];
}>();

const resolvedPreset = computed(() => getDefaultStatePreset(props.state));

function resolveActionIcon(icon?: string): string {
  if (!icon) {
    return "";
  }

  return ACTION_ICONS[icon] ?? icon;
}

function resolveAction(
  action: DefaultStateAction | undefined,
  label: string | undefined,
  icon: string | undefined,
) {
  const resolvedLabel = label ?? action?.label;
  if (!resolvedLabel) {
    return null;
  }

  return {
    label: resolvedLabel,
    icon: resolveActionIcon(icon ?? action?.icon),
  };
}

const resolvedPrimaryAction = computed(() =>
  resolveAction(
    resolvedPreset.value.primaryAction,
    props.primaryLabel,
    props.primaryIcon,
  ),
);

const resolvedSecondaryAction = computed(() =>
  resolveAction(
    resolvedPreset.value.secondaryAction,
    props.secondaryLabel,
    props.secondaryIcon,
  ),
);

function emitPrimary() {
  emit("primary");
}

function emitSecondary() {
  emit("secondary");
}

function handleBack() {
  emit("back");
}
</script>

<style scoped>
.default-state-page {
  position: relative;
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  background: #f7fbef;
}

.default-state-page.with-tab-bar {
  padding-bottom: 132rpx;
}

.default-page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.back-control {
  position: relative;
  z-index: 2;
  width: 78rpx;
  height: 78rpx;
  margin: 42rpx 0 0 30rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12rpx 34rpx rgba(43, 92, 36, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  color: #2d8235;
  font-size: 58rpx;
  font-weight: 500;
  line-height: 1;
  transform: translateY(-2rpx);
}

.default-state-content {
  position: relative;
  z-index: 1;
  height: 100%;
  box-sizing: border-box;
  padding: 64rpx 34rpx 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.with-tab-bar .default-state-content {
  padding-top: 58rpx;
  padding-bottom: 22rpx;
}

.state-heading {
  width: 100%;
  text-align: center;
  flex: 0 0 auto;
}

.heading-title {
  display: block;
  color: #2f7d2e;
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 60rpx;
  font-weight: 900;
  line-height: 1.12;
  letter-spacing: 3rpx;
  text-shadow: 0 7rpx 16rpx rgba(58, 127, 47, 0.12);
}

.heading-subtitle {
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: #6a7078;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 1.2;
}

.leaf {
  color: #99bf83;
  font-size: 24rpx;
}

.state-card {
  position: relative;
  width: 100%;
  max-width: 684rpx;
  flex: 1;
  min-height: 0;
  margin-top: 48rpx;
  box-sizing: border-box;
  border: 2rpx solid rgba(231, 240, 226, 0.82);
  border-radius: 58rpx;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.92), 0 18rpx 44rpx rgba(64, 102, 60, 0.08);
  padding: 42rpx 46rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

.with-tab-bar .state-card {
  margin-top: 34rpx;
  border-radius: 44rpx;
  padding: 34rpx 42rpx 32rpx;
}

.sparkle {
  position: absolute;
  width: 20rpx;
  height: 20rpx;
  transform: rotate(45deg);
  border-radius: 4rpx;
  background: rgba(67, 141, 53, 0.8);
}

.sparkle-one {
  top: 88rpx;
  left: 148rpx;
}

.sparkle-two {
  top: 150rpx;
  right: 126rpx;
  opacity: 0.22;
}

.state-illustration {
  width: 100%;
  height: 334rpx;
  flex: 0 0 auto;
}

.with-tab-bar .state-illustration {
  height: 250rpx;
}

.state-title {
  margin-top: 30rpx;
  color: #2f7d2e;
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 48rpx;
  font-weight: 900;
  line-height: 1.18;
  letter-spacing: 3rpx;
  text-align: center;
}

.with-tab-bar .state-title {
  margin-top: 22rpx;
  font-size: 40rpx;
}

.state-description {
  display: block;
  max-width: 540rpx;
  margin-top: 22rpx;
  color: #626a75;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.58;
  text-align: center;
}

.with-tab-bar .state-description {
  margin-top: 16rpx;
  font-size: 24rpx;
  line-height: 1.48;
}

.state-action {
  width: 100%;
  height: 86rpx;
  margin: 34rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 24rpx;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 86rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.with-tab-bar .state-action {
  height: 76rpx;
  margin-top: 24rpx;
  border-radius: 22rpx;
  font-size: 27rpx;
  line-height: 76rpx;
}

.state-action::after {
  border: 0;
}

.primary-action {
  color: #ffffff;
  background: linear-gradient(90deg, #338a32 0%, #28772d 100%);
  box-shadow: 0 15rpx 30rpx rgba(45, 122, 45, 0.2);
}

.state-action-hover {
  transform: translateY(2rpx);
  opacity: 0.9;
}

.secondary-action {
  margin-top: 22rpx;
  border: 2rpx solid rgba(191, 217, 184, 0.82);
  color: #2f7d2e;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: none;
}

.with-tab-bar .secondary-action {
  margin-top: 16rpx;
}

.secondary-action-hover {
  background: rgba(240, 248, 236, 0.92);
}

.action-icon,
.secondary-action-icon {
  font-size: 34rpx;
  line-height: 1;
}

.secondary-action-icon {
  color: #2f7d2e;
}
</style>
