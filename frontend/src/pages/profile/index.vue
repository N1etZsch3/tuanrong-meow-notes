<template>
  <view class="page">
    <DefaultState
      state="under_development"
      title="个人中心建设中"
      description="个人资料、任务记录、通知入口和管理员入口正在接入。"
      primary-label="刷新页面"
      primary-icon="refresh"
      secondary-label="返回地图"
      secondary-icon="map"
      with-tab-bar
      @primary="refreshPage"
      @secondary="goMap"
    />
    <AppTabBar active-key="profile" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";
import DefaultState from "@/components/DefaultState.vue";

function refreshPage() {
  uni.showToast({ title: "个人中心暂未接入", icon: "none" });
}

function goMap() {
  uni.reLaunch({ url: "/pages/index/index" });
}
</script>

<style scoped>
.page {
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
}
</style>
