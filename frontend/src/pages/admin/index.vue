<template>
  <view class="admin-page">
    <view class="admin-inner">
      <view class="nav-row">
        <button class="back-button" @tap="goBack">‹</button>
        <view>
          <text class="nav-title">管理员入口</text>
          <text class="nav-subtitle">成员账号、喂食任务与物资点</text>
        </view>
      </view>

      <view v-if="!userStore.isAdmin" class="permission-card">
        <text class="permission-title">暂无管理员权限</text>
        <text class="permission-copy">该入口仅管理员可见。</text>
      </view>

      <view v-else class="admin-actions">
        <button class="admin-action" @tap="goCreateUser">
          <view class="action-icon">＋</view>
          <view class="action-copy">
            <text class="action-title">添加账户</text>
            <text class="action-subtitle">创建成员喵喵号并要求首次登录改密</text>
          </view>
          <text class="action-chevron">›</text>
        </button>

        <button class="admin-action" @tap="goPublishTask">
          <view class="action-icon action-icon-task">食</view>
          <view class="action-copy">
            <text class="action-title">发布喂食任务</text>
            <text class="action-subtitle">创建暑假投喂点、日期、物资和图片</text>
          </view>
          <text class="action-chevron">›</text>
        </button>

        <button class="admin-action" @tap="goCreateSupplyPoint">
          <view class="action-icon action-icon-supply">物</view>
          <view class="action-copy">
            <text class="action-title">新建物资点</text>
            <text class="action-subtitle">创建地图物资点、配置初始物资和路线照片</text>
          </view>
          <text class="action-chevron">›</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";

const userStore = useUserStore();

function goCreateUser() {
  uni.navigateTo({ url: "/pages/admin/create-user" });
}

function goPublishTask() {
  uni.navigateTo({ url: "/pages/admin/tasks/create" });
}

function goCreateSupplyPoint() {
  uni.navigateTo({ url: "/pages/admin/supplies/create" });
}

function goBack() {
  uni.navigateBack();
}
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fbfcfb 0%, #f5faef 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.admin-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #ffffff;
  color: #2f8037;
  font-size: 58rpx;
  line-height: 54rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.1);
}

.back-button::after,
.admin-action::after {
  border: 0;
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
  color: #68717a;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  line-height: 1.2;
}

.admin-actions {
  margin-top: 34rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.admin-action,
.permission-card {
  box-sizing: border-box;
  width: 100%;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
}

.admin-action {
  min-height: 142rpx;
  padding: 26rpx 30rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
  text-align: left;
}

.action-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 48rpx;
  line-height: 66rpx;
  text-align: center;
}

.action-icon-task {
  background: #ff8b22;
}

.action-icon-supply {
  background: #287c31;
  font-size: 34rpx;
  line-height: 72rpx;
}

.action-copy {
  min-width: 0;
  flex: 1;
}

.action-title,
.action-subtitle,
.permission-title,
.permission-copy {
  display: block;
}

.action-title {
  color: #20242a;
  font-size: 31rpx;
  font-weight: 900;
}

.action-subtitle {
  margin-top: 6rpx;
  color: #69727b;
  font-size: 24rpx;
  line-height: 1.3;
}

.action-chevron {
  color: #68717a;
  font-size: 52rpx;
}

.permission-card {
  margin-top: 44rpx;
  padding: 42rpx 34rpx;
}

.permission-title {
  color: #20242a;
  font-size: 31rpx;
  font-weight: 900;
}

.permission-copy {
  margin-top: 14rpx;
  color: #69727b;
  font-size: 25rpx;
}
</style>
