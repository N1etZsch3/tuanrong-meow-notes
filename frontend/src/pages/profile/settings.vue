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

        <view class="settings-card">
          <button class="settings-row" @tap="goResetPassword">
            <image class="row-icon" :src="passwordIcon" mode="aspectFit" />
            <view class="row-copy">
              <text class="row-title">重设密码</text>
              <text class="row-desc">修改当前账号的登录密码</text>
            </view>
            <text class="row-chevron">›</text>
          </button>
        </view>

        <button class="logout-button" @tap="confirmLogout">退出登录</button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import passwordIcon from "../../../素材/svg/登录页/修改密码.svg";
import pageBackground from "../../../素材/加载页素材/背景.jpg";

const userStore = useUserStore();

function goBack() {
  uni.navigateBack();
}

function goResetPassword() {
  uni.navigateTo({ url: "/pages/profile/reset-password" });
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
  padding: 78rpx 38rpx calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 22rpx;
  margin-bottom: 38rpx;
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
.settings-row::after,
.logout-button::after {
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
  font-size: 48rpx;
  font-weight: 900;
  line-height: 1.08;
}

.nav-subtitle {
  margin-top: 12rpx;
  color: #656d78;
  font-size: 24rpx;
  font-weight: 700;
}

.settings-card {
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
  padding: 10rpx 28rpx;
}

.settings-row {
  min-height: 116rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 20rpx;
  text-align: left;
}

.row-icon {
  width: 48rpx;
  height: 48rpx;
  filter: brightness(0) saturate(100%) invert(36%) sepia(33%) saturate(1009%) hue-rotate(75deg) brightness(92%) contrast(91%);
  flex: 0 0 auto;
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
  font-size: 30rpx;
  font-weight: 900;
}

.row-desc {
  margin-top: 10rpx;
  color: #707883;
  font-size: 23rpx;
}

.row-chevron {
  color: #79818b;
  font-size: 48rpx;
  line-height: 1;
}

.logout-button {
  width: 100%;
  height: 88rpx;
  margin: 32rpx 0 0;
  border-radius: 26rpx;
  background: #fff5f2;
  color: #c34839;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 88rpx;
}
</style>
