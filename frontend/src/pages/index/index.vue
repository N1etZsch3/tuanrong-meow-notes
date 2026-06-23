<template>
  <view class="page">
    <view class="card">
      <text class="title">猫协地图</text>
      <text class="subtitle">登录成功后的首页占位</text>
    </view>
  </view>
</template>

<script setup lang="ts"></script>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f6faf0;
  padding: 48rpx;
}

.card {
  width: 100%;
  border-radius: 32rpx;
  background: #ffffff;
  box-shadow: 0 18rpx 42rpx rgba(43, 92, 36, 0.1);
  padding: 56rpx 40rpx;
}

.title {
  display: block;
  color: #26742b;
  font-size: 48rpx;
  font-weight: 700;
  text-align: center;
}

.subtitle {
  display: block;
  margin-top: 18rpx;
  color: #6f756f;
  font-size: 28rpx;
  text-align: center;
}
</style>
