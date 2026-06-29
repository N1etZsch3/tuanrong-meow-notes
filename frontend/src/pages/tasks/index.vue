<template>
  <view class="tasks-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="task-scroll" scroll-y :show-scrollbar="false">
      <view class="task-inner">
        <view class="page-title">
          <view class="title-copy">
            <view class="title-row">
              <text class="title-text">任务</text>
              <image class="title-icon" :src="pawIcon" mode="aspectFit" />
            </view>
            <text class="title-subtitle">暑假投喂安排</text>
          </view>
        </view>

        <view class="toolbar">
          <button
            class="filter-chip"
            :class="{ 'is-active': onlyToday }"
            hover-class="button-hover"
            @tap="toggleToday"
          >
            今日任务
          </button>
          <button class="filter-chip" hover-class="button-hover" @tap="loadTasks">
            刷新
          </button>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载投喂任务</text>
          <text class="state-copy">稍等一下，任务列表马上就好。</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">任务加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
        </view>

        <view v-else-if="tasks.length" class="task-list">
          <button
            v-for="task in tasks"
            :key="task.task_id"
            class="task-card"
            hover-class="task-card-hover"
            @tap="goDetail(task.task_id)"
          >
            <view class="task-image-wrap">
              <image
                v-if="task.cover_photo_url"
                class="task-image"
                :src="task.cover_photo_url"
                mode="aspectFill"
              />
              <view v-else class="task-image-placeholder">
                <image class="placeholder-icon" :src="taskIcon" mode="aspectFit" />
              </view>
            </view>
            <view class="task-main">
              <view class="task-head">
                <text class="task-title">{{ task.title }}</text>
                <text class="task-status">{{ getTaskListStatusLabel(task) }}</text>
              </view>
              <text class="task-location">{{ task.map_point.location_name }}</text>
              <text class="task-desc">{{ task.description }}</text>
              <view class="task-meta">
                <text>{{ executionText(task) }}</text>
                <text>{{ task.required_items }}</text>
              </view>
            </view>
          </button>
        </view>

        <view v-else class="state-box">
          <text class="state-title">暂无投喂任务</text>
          <text class="state-copy">发布后的喂食点会显示在这里和地图上。</text>
        </view>
      </view>
    </scroll-view>
    <AppTabBar active-key="tasks" />
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";

import { getTasks, type TaskListItemDto } from "@/api/tasks";
import AppTabBar from "@/components/AppTabBar.vue";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import { formatTaskDate, getTaskListStatusLabel } from "@/pages/tasks/task-page";

import taskIcon from "../../../素材/icon/任务.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/加载页背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const tasks = ref<TaskListItemDto[]>([]);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const onlyToday = ref(false);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function executionText(task: TaskListItemDto): string {
  const current = task.current_execution || task.next_execution;
  if (!current) {
    return "暂无执行日期";
  }

  const label = current.status === "completed" ? "已完成" : "待投喂";
  return `${formatTaskDate(current.execute_date)} · ${label}`;
}

async function loadTasks() {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  loadState.value = "loading";
  try {
    const data = await getTasks(token, {
      task_type: "feeding",
      status: "in_progress,completed",
      only_today: onlyToday.value || undefined,
      page: 1,
      page_size: 50,
    });
    tasks.value = data.items;
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function toggleToday() {
  onlyToday.value = !onlyToday.value;
  void loadTasks();
}

function goDetail(taskId: string) {
  uni.navigateTo({ url: `/pages/tasks/detail?task_id=${taskId}` });
}

onShow(() => {
  void loadTasks();
});
</script>

<style scoped>
.tasks-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #111827;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.task-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.task-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 164rpx);
}

.page-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
}

.title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.filter-chip::after,
.task-card::after {
  border: 0;
}

.toolbar {
  margin-top: 40rpx;
  display: flex;
  gap: 18rpx;
}

.filter-chip {
  height: 64rpx;
  margin: 0;
  padding: 0 28rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.35);
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.9);
  color: #287c31;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 60rpx;
}

.filter-chip.is-active {
  background: #287c31;
  color: #ffffff;
}

.task-list {
  margin-top: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.task-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 206rpx;
  margin: 0;
  padding: 20rpx;
  border: 0;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.1);
  color: #111827;
  display: grid;
  grid-template-columns: 152rpx minmax(0, 1fr);
  gap: 20rpx;
  text-align: left;
}

.task-card-hover,
.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.task-image-wrap,
.task-image,
.task-image-placeholder {
  width: 152rpx;
  height: 152rpx;
  border-radius: 22rpx;
  overflow: hidden;
}

.task-image-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 86rpx;
  height: 86rpx;
}

.task-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.task-head {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.task-title {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.25;
}

.task-status {
  flex-shrink: 0;
  padding: 7rpx 12rpx;
  border-radius: 12rpx;
  background: #e9f7e9;
  color: #287c31;
  font-size: 20rpx;
  font-weight: 900;
}

.task-location,
.task-desc,
.task-meta {
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.4;
}

.task-desc {
  color: #4b5563;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.state-box {
  margin-top: 42rpx;
  box-sizing: border-box;
  padding: 46rpx 34rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.08);
}

.state-title,
.state-copy {
  display: block;
}

.state-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 14rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.5;
}
</style>
