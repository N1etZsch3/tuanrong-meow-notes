<template>
  <view class="settings-page">
    <image class="page-bg" :src="pageBackground" mode="aspectFill" />
    <scroll-view class="settings-scroll" scroll-y :show-scrollbar="false">
      <view class="settings-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="nav-copy">
            <text class="nav-title">账号设置</text>
            <text class="nav-subtitle">管理登录密码与当前会话</text>
          </view>
        </view>

        <view class="settings-section">
          <text class="section-title">账号与安全</text>
          <view class="settings-group">
            <button class="settings-row" @tap="goResetPassword">
              <view class="row-icon-shell">
                <image class="row-icon" :src="passwordIcon" mode="aspectFit" />
              </view>
              <text class="row-title">重设密码</text>
              <text class="row-chevron">›</text>
            </button>
            <view class="row-divider" />
            <button
              class="settings-row"
              :disabled="isUnbindingWechat"
              @tap="confirmWechatUnbind"
            >
              <view class="row-icon-shell is-wechat">
                <image class="row-icon" :src="wechatIcon" mode="aspectFit" />
              </view>
              <text class="row-title">微信解绑</text>
              <text class="row-chevron">›</text>
            </button>
          </view>
        </view>

        <view class="settings-section logout-section">
          <view class="settings-group">
            <button class="settings-row logout-row" @tap="confirmLogout">
              <text class="logout-title">退出登录</text>
            </button>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import passwordIcon from "../../../素材/svg/登录页/修改密码.svg";
import wechatIcon from "../../../素材/svg/用户页/设置.svg";
import pageBackground from "../../../素材/加载页素材/背景.jpg";

const userStore = useUserStore();
const isUnbindingWechat = ref(false);

function goBack() {
  uni.navigateBack();
}

function goResetPassword() {
  uni.navigateTo({ url: "/pages/profile/reset-password" });
}

function confirmWechatUnbind() {
  if (isUnbindingWechat.value) {
    return;
  }
  uni.showModal({
    title: "微信解绑",
    content: "解绑后将立即退出登录。下次进入小程序时，需要使用喵喵号和密码重新登录并绑定当前微信。",
    confirmText: "确认解绑",
    confirmColor: "#c34839",
    success: (result) => {
      if (result.confirm) {
        void unbindWechat();
      }
    },
  });
}

async function unbindWechat() {
  if (isUnbindingWechat.value) {
    return;
  }
  isUnbindingWechat.value = true;
  try {
    await userStore.unbindCurrentWechat();
    uni.reLaunch({ url: LOGIN_ROUTE });
  } catch (error) {
    const message = error instanceof Error ? error.message : "微信解绑失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUnbindingWechat.value = false;
  }
}

function confirmLogout() {
  uni.showModal({
    title: "退出登录",
    content: "确认退出当前账号吗？",
    confirmText: "退出",
    success: async (result) => {
      if (!result.confirm) {
        return;
      }
      try {
        await userStore.logoutFromServer();
      } finally {
        uni.reLaunch({ url: LOGIN_ROUTE });
      }
    },
  });
}
</script>

<style scoped>
.settings-page {
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

.settings-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.settings-inner {
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

.back-button::after,
.settings-row::after {
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

.settings-section + .settings-section {
  margin-top: 30rpx;
}

.section-title {
  display: block;
  margin: 0 18rpx 12rpx;
  color: #6f7781;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0;
}

.settings-group {
  overflow: hidden;
  border: 1rpx solid rgba(207, 218, 208, 0.72);
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8rpx 24rpx rgba(42, 63, 43, 0.07);
}

.settings-row {
  box-sizing: border-box;
  width: 100%;
  min-height: 94rpx;
  margin: 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 18rpx;
  text-align: left;
  line-height: 1;
}

.settings-row[disabled] {
  opacity: 0.58;
}

.row-icon-shell {
  width: 50rpx;
  height: 50rpx;
  border-radius: 12rpx;
  background: #edf6ea;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.row-icon-shell.is-wechat {
  background: #edf7f0;
}

.row-icon {
  width: 30rpx;
  height: 30rpx;
  filter: brightness(0) saturate(100%) invert(36%) sepia(33%) saturate(1009%) hue-rotate(75deg) brightness(92%) contrast(91%);
}

.row-divider {
  height: 1rpx;
  margin-left: 92rpx;
  background: rgba(210, 218, 213, 0.74);
}

.row-title {
  min-width: 0;
  flex: 1;
  color: #22272f;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
}

.row-chevron {
  color: #8b929a;
  font-size: 40rpx;
  line-height: 1;
}

.logout-section {
  margin-top: 36rpx;
}

.logout-row {
  justify-content: center;
}

.logout-title {
  color: #c34839;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
}
</style>
