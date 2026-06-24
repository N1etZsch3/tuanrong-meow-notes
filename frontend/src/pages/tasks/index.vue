<template>
  <view class="page">
    <DefaultState
      state="under_development"
      title="任务模块建设中"
      description="任务列表、多人接取和打卡流程正在接入。"
      primary-label="刷新任务"
      primary-icon="refresh"
      secondary-label="返回地图"
      secondary-icon="map"
      with-tab-bar
      @primary="refreshPage"
      @secondary="goMap"
    />
    <AppTabBar active-key="tasks" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";
import DefaultState from "@/components/DefaultState.vue";

function refreshPage() {
  uni.showToast({ title: "任务数据暂未接入", icon: "none" });
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
