<template>
  <view class="detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">任务详情</text>
            <text class="nav-subtitle">查看本次投喂信息与历史动态</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载任务详情</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">任务详情加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
        </view>

        <view v-else-if="task" class="detail-content">
          <view class="hero-card">
            <swiper
              v-if="heroPhotos.length"
              class="hero-swiper"
              :autoplay="true"
              :interval="5000"
              :duration="400"
              :circular="true"
            >
              <swiper-item
                v-for="photo in heroPhotos"
                :key="photo.photo_id"
                class="hero-slide"
              >
                <image
                  class="hero-image"
                  :src="photo.url"
                  mode="aspectFill"
                  @error="markHeroPhotoFailed(photo.photo_id)"
                />
              </swiper-item>
            </swiper>
            <view v-else class="hero-placeholder">
              <image class="hero-placeholder-icon" :src="taskIcon" mode="aspectFit" />
            </view>
          </view>

          <view class="title-block">
            <text class="eyebrow">喂食点名称</text>
            <text class="task-title">{{ task.title }}</text>
            <text class="task-desc">{{ task.description }}</text>
          </view>

          <view class="info-grid">
            <view class="info-card">
              <text class="info-label">本次任务日期</text>
              <text class="info-value">{{ currentDateText }}</text>
            </view>
            <view class="info-card">
              <text class="info-label">地址</text>
              <text class="info-value">
                {{ task.map_point.location_name }}{{ task.map_point.location_detail ? `，${task.map_point.location_detail}` : "" }}
              </text>
            </view>
          </view>

          <view class="section-card">
            <text class="section-title">任务要求</text>
            <text class="section-line">物资：{{ task.required_items }}</text>
            <text class="section-line">说明：{{ task.description }}</text>
            <text class="section-line">
              路线：{{ task.map_point.route_instruction || "暂无路线说明" }}
            </text>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">任务动态</text>
              <text class="section-meta">{{ task.activities.length }} 条</text>
            </view>
            <view v-if="task.activities.length" class="timeline">
              <view
                v-for="activity in task.activities"
                :key="activity.activity_id"
                class="timeline-row"
              >
                <view class="timeline-dot" />
                <view class="timeline-copy">
                  <text class="timeline-title">{{ activity.title }}</text>
                  <text class="timeline-content">{{ activity.content || "暂无备注" }}</text>
                  <text class="timeline-time">{{ formatActivityTime(activity.created_at) }}</text>
                </view>
              </view>
            </view>
            <text v-else class="empty-line">暂无任务动态</text>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">完成照片</text>
              <button
                class="small-button"
                :loading="isUploading"
                hover-class="button-hover"
                @tap="chooseCheckinPhoto"
              >
                上传
              </button>
            </view>
            <view v-if="checkinPhotos.length" class="photo-strip">
              <image
                v-for="photo in checkinPhotos"
                :key="photo.file_id"
                class="checkin-photo"
                :src="photo.thumbnail_url || photo.file_url"
                mode="aspectFill"
              />
            </view>
            <text v-else class="empty-line">完成投喂前可上传现场照片</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="task" class="bottom-actions">
      <button class="ghost-action" hover-class="button-hover" @tap="showNavigationTodo">
        导航前往
      </button>
      <button
        class="primary-action"
        :loading="isSubmitting"
        :disabled="!canCheckin"
        hover-class="button-hover"
        @tap="completeFeedingTask"
      >
        完成投喂
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { buildFileAssetContentUrl, uploadImage } from "@/api/files";
import {
  checkinTask,
  getTaskDetail,
  type TaskDetailDto,
  type TaskPhotoDto,
  type UploadedFileRef,
} from "@/api/tasks";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import { buildUploadedTaskPhoto, formatTaskDate } from "@/pages/tasks/task-page";
import { clearTaskListCache } from "@/pages/tasks/task-list-cache";

import taskIcon from "../../../素材/icon/任务.png";
import loadingBackground from "../../../素材/加载页素材/加载页背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const taskId = ref("");
const task = ref<TaskDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const isUploading = ref(false);
const isSubmitting = ref(false);
const checkinPhotos = ref<UploadedFileRef[]>([]);
const failedHeroPhotoIds = ref<string[]>([]);

const heroPhotos = computed(() => {
  if (!task.value) {
    return [];
  }

  const failed = new Set(failedHeroPhotoIds.value);
  return task.value.photos
    .map((photo) => ({
      photo_id: photo.photo_id,
      url: getTaskPhotoUrl(photo, "task_detail_full"),
    }))
    .filter((photo) => photo.url && !failed.has(photo.photo_id));
});
const currentExecution = computed(() => task.value?.current_execution || task.value?.next_execution || null);
const currentDateText = computed(() => formatTaskDate(currentExecution.value?.execute_date));
const canCheckin = computed(() => Boolean(task.value?.actions.can_checkin && currentExecution.value));

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function formatActivityTime(value: string): string {
  return value ? value.replace("T", " ").slice(0, 16) : "";
}

function getTaskPhotoUrl(
  photo: TaskPhotoDto | undefined,
  scene: "task_detail_full" | "task_list_cover",
): string {
  if (!photo) {
    return "";
  }

  return photo.file_id
    ? buildFileAssetContentUrl(photo.file_id, scene)
    : photo.file_url;
}

function markHeroPhotoFailed(photoId: string) {
  if (!failedHeroPhotoIds.value.includes(photoId)) {
    failedHeroPhotoIds.value = [...failedHeroPhotoIds.value, photoId];
  }
}

async function loadTaskDetail() {
  const token = await getAccessToken();
  if (!token || !taskId.value) {
    return;
  }

  loadState.value = "loading";
  try {
    task.value = await getTaskDetail(token, taskId.value);
    failedHeroPhotoIds.value = [];
    checkinPhotos.value = [];
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function chooseCheckinPhoto() {
  uni.chooseImage({
    count: 3,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths].filter(Boolean);
      void uploadCheckinPhotos(paths);
    },
  });
}

async function uploadCheckinPhotos(paths: string[]) {
  const token = await getAccessToken();
  if (!token || !paths.length) {
    return;
  }

  isUploading.value = true;
  try {
    for (const path of paths) {
      const asset = await uploadImage(token, path, {
        usage_type: "task_checkin_photo",
        owner_type: "task_checkin",
        visibility: "internal",
        caption: "投喂完成照片",
      });
      checkinPhotos.value = [...checkinPhotos.value, buildUploadedTaskPhoto(asset)];
    }
    uni.showToast({ title: "照片已上传", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploading.value = false;
  }
}

async function completeFeedingTask() {
  const token = await getAccessToken();
  if (!token || !task.value || !currentExecution.value || isSubmitting.value) {
    return;
  }

  if (!canCheckin.value) {
    uni.showToast({
      title: task.value.actions.checkin_disabled_reason || "当前不可完成",
      icon: "none",
    });
    return;
  }

  isSubmitting.value = true;
  try {
    await checkinTask(token, task.value.task_id, {
      execute_date: currentExecution.value.execute_date,
      is_completed: true,
      process_result: "已完成投喂",
      remark: "",
      photos: checkinPhotos.value,
    });
    uni.showToast({ title: "投喂已完成", icon: "success" });
    clearTaskListCache();
    await loadTaskDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "提交失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function showNavigationTodo() {
  uni.showToast({ title: "导航后续接入", icon: "none" });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  taskId.value = typeof query?.task_id === "string" ? query.task_id : "";
  void loadTaskDetail();
});
</script>

<style scoped>
.detail-page {
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

.detail-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.detail-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 170rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.small-button::after,
.ghost-action::after,
.primary-action::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.state-title,
.state-copy,
.eyebrow,
.task-title,
.task-desc,
.info-label,
.info-value,
.section-title,
.section-line,
.section-meta,
.empty-line,
.timeline-title,
.timeline-content,
.timeline-time {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: 44rpx;
  font-weight: 900;
}

.nav-subtitle {
  margin-top: 8rpx;
  color: #526070;
  font-size: 24rpx;
  font-weight: 700;
}

.detail-content {
  margin-top: 38rpx;
}

.hero-card,
.hero-swiper,
.hero-slide,
.hero-image,
.hero-placeholder {
  width: 100%;
  height: 388rpx;
  border-radius: 28rpx;
  overflow: hidden;
}

.hero-card {
  box-shadow: 0 18rpx 42rpx rgba(27, 54, 30, 0.12);
}

.hero-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-placeholder-icon {
  width: 150rpx;
  height: 150rpx;
}

.title-block {
  margin-top: 34rpx;
}

.eyebrow {
  color: #6f7a65;
  font-size: 24rpx;
  font-weight: 800;
}

.task-title {
  margin-top: 12rpx;
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.task-desc {
  margin-top: 18rpx;
  color: #465160;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
}

.info-grid {
  margin-top: 34rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.info-card,
.section-card,
.state-box {
  box-sizing: border-box;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.info-card {
  min-height: 156rpx;
  padding: 26rpx;
}

.info-label,
.section-meta,
.empty-line,
.timeline-time {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.info-value {
  margin-top: 14rpx;
  color: #111827;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.35;
}

.section-card,
.state-box {
  margin-top: 24rpx;
  padding: 30rpx;
}

.state-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.section-line {
  margin-top: 16rpx;
  color: #465160;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 1.55;
}

.timeline {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.timeline-row {
  display: grid;
  grid-template-columns: 24rpx minmax(0, 1fr);
  gap: 18rpx;
}

.timeline-dot {
  width: 16rpx;
  height: 16rpx;
  margin-top: 10rpx;
  border-radius: 50%;
  background: #287c31;
  box-shadow: 0 0 0 8rpx rgba(40, 124, 49, 0.12);
}

.timeline-title {
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
}

.timeline-content {
  margin-top: 8rpx;
  color: #243042;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.45;
}

.timeline-time {
  margin-top: 7rpx;
}

.small-button {
  width: 108rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #e9f7e9;
  color: #287c31;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.photo-strip {
  margin-top: 22rpx;
  display: flex;
  gap: 14rpx;
  overflow: hidden;
}

.checkin-photo {
  width: 126rpx;
  height: 126rpx;
  border-radius: 20rpx;
}

.empty-line {
  margin-top: 20rpx;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.18fr);
  gap: 20rpx;
}

.ghost-action,
.primary-action {
  height: 92rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 30rpx;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 92rpx;
}

.ghost-action {
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.1);
}

.primary-action {
  background: #287c31;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.primary-action[disabled] {
  background: #a7b7a6;
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
