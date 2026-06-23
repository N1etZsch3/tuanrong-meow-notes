<template>
  <view class="page">
    <DefaultState
      state="under_development"
      title="地图建设中"
      description="校园地图、任务点、猫咪点和物资点正在接入。"
      primary-label="刷新地图"
      primary-icon="refresh"
      secondary-label="先去任务看看"
      secondary-icon="paw"
      with-tab-bar
      @primary="refreshPage"
      @secondary="goTasks"
    />
    <AppTabBar active-key="map" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";
import DefaultState from "@/components/DefaultState.vue";

function refreshPage() {
  uni.showToast({ title: "地图数据暂未接入", icon: "none" });
}

function goTasks() {
  uni.reLaunch({ url: "/pages/tasks/index" });
}
</script>

<style scoped>
.page {
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
}
</style>
