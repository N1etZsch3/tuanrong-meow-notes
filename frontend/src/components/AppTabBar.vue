<template>
  <view class="tab-bar-safe">
    <view class="app-tab-bar">
      <button
        v-for="item in APP_TAB_ITEMS"
        :key="item.key"
        class="tab-item"
        :class="[
          `tab-item-${item.key}`,
          {
            'is-active': item.key === currentActiveKey,
            'preserve-active-icon': item.preserveActiveIconColor,
          },
        ]"
        hover-class="tab-item-hover"
        :aria-label="`切换到${item.label}`"
        @tap="handleTabTap(item.key)"
      >
        <view class="tab-icon-shell">
          <image class="tab-icon" :src="item.icon" mode="aspectFit" />
        </view>
        <text class="tab-label">{{ item.label }}</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

import {
  APP_TAB_ITEMS,
  getActiveTabKey,
  getTabTarget,
  shouldNavigateTab,
  type AppTabKey,
} from "./app-tab-bar";

const props = defineProps<{
  activeKey?: AppTabKey;
  currentRoute?: string;
}>();

const currentActiveKey = computed(
  () => props.activeKey ?? getActiveTabKey(props.currentRoute ?? ""),
);

onMounted(() => {
  uni.hideTabBar({
    fail: () => {
      // Ignore error if the current context isn't considered a tab bar page yet
    },
  });
});

function handleTabTap(tabKey: AppTabKey) {
  if (tabKey === currentActiveKey.value) {
    return;
  }

  if (!shouldNavigateTab(tabKey, props.currentRoute ?? "")) {
    return;
  }

  uni.switchTab({
    url: getTabTarget(tabKey),
  });
}
</script>

<style scoped>
.tab-bar-safe {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  box-sizing: border-box;
  padding: 0 24rpx 8rpx;
  pointer-events: none;
}

.app-tab-bar {
  width: 100%;
  height: 112rpx;
  box-sizing: border-box;
  border: 2rpx solid rgba(220, 231, 218, 0.84);
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 -4rpx 22rpx rgba(46, 82, 48, 0.06), 0 18rpx 46rpx rgba(26, 52, 30, 0.12);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: center;
  backdrop-filter: blur(16rpx);
  pointer-events: auto;
}

.tab-item {
  position: relative;
  min-width: 0;
  height: 100rpx;
  margin: 0;
  padding: 8rpx 0 6rpx;
  border: 0;
  border-radius: 34rpx;
  background: transparent;
  color: #6f747c;
  line-height: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  overflow: visible;
  transition: transform 0.2s ease, color 0.2s ease;
}

.tab-item::after {
  border: 0;
}

.tab-item-hover {
  transform: translateY(-4rpx);
}

.tab-icon-shell {
  width: 52rpx;
  height: 52rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.24s ease, background 0.24s ease, box-shadow 0.24s ease;
}

.tab-icon {
  width: 44rpx;
  height: 44rpx;
  filter: grayscale(1) saturate(0) opacity(0.72);
  transition: filter 0.24s ease, transform 0.24s ease;
}

.tab-label {
  color: currentColor;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.1;
  transition: color 0.2s ease, transform 0.2s ease;
}

.tab-item.is-active {
  color: #267b2f;
}

.tab-item.is-active .tab-icon-shell {
  background: linear-gradient(180deg, rgba(226, 245, 221, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
  box-shadow: 0 10rpx 24rpx rgba(42, 120, 48, 0.16);
  transform: translateY(-8rpx) scale(1.04);
  animation: tabPop 0.28s ease-out both;
}

.tab-item.is-active .tab-icon {
  filter: brightness(0) saturate(100%) invert(33%) sepia(32%) saturate(1136%) hue-rotate(75deg) brightness(92%) contrast(91%);
  transform: scale(1.05);
}

.tab-item.is-active.preserve-active-icon .tab-icon {
  filter: none;
}

.tab-item.is-active .tab-label {
  transform: translateY(-2rpx);
}

@keyframes tabPop {
  0% {
    transform: translateY(0) scale(0.92);
  }

  70% {
    transform: translateY(-10rpx) scale(1.08);
  }

  100% {
    transform: translateY(-8rpx) scale(1.04);
  }
}
</style>
