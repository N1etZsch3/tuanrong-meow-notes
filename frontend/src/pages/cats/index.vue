<template>
  <view class="page">
    <DefaultState
      state="under_development"
      title="猫咪库建设中"
      description="猫咪档案、搜索筛选和最近出现记录正在整理。"
      primary-label="刷新猫咪库"
      primary-icon="refresh"
      secondary-label="返回地图"
      secondary-icon="map"
      with-tab-bar
      @primary="refreshPage"
      @secondary="goMap"
    />
    <AppTabBar active-key="cats" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";
import DefaultState from "@/components/DefaultState.vue";

function refreshPage() {
  uni.showToast({ title: "猫咪档案暂未接入", icon: "none" });
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
