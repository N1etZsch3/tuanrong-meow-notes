<template>
  <view class="page">
    <view class="hero">
      <text class="title">猫咪库</text>
      <text class="subtitle">查询校园猫咪档案</text>
    </view>
    <view class="placeholder-card">
      <text class="placeholder-title">猫咪库页面待开发</text>
      <text class="placeholder-text">后续接入猫咪列表、搜索筛选、健康状态和最近出现记录。</text>
    </view>
    <AppTabBar active-key="cats" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";
</script>

<style scoped>
.page {
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  background: #f6faf0;
  padding: 78rpx 36rpx 150rpx;
}

.hero {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.title {
  color: #1f7228;
  font-size: 52rpx;
  font-weight: 900;
  letter-spacing: 3rpx;
  line-height: 1.15;
}

.subtitle {
  color: #5f666e;
  font-size: 28rpx;
  font-weight: 600;
}

.placeholder-card {
  margin-top: 42rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18rpx 42rpx rgba(43, 92, 36, 0.1);
  padding: 44rpx 36rpx;
}

.placeholder-title {
  display: block;
  color: #1f2521;
  font-size: 33rpx;
  font-weight: 800;
}

.placeholder-text {
  display: block;
  margin-top: 16rpx;
  color: #6a716c;
  font-size: 25rpx;
  line-height: 1.55;
}
</style>
