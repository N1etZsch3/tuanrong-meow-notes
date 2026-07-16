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
          <button class="retry-button" hover-class="button-hover" @tap="retryTaskDetail">
            重新加载
          </button>
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
                  @tap="openTaskPhotoPreview(photo.photo_id)"
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
            <view class="task-title-row">
              <text class="task-title">{{ task.title }}</text>
              <button
                v-if="canAdminEditTask"
                class="task-edit-button"
                hover-class="button-hover"
                @tap="goEditTask"
              >
                编辑
              </button>
            </view>
            <text class="task-desc">{{ task.description }}</text>
          </view>

          <view class="task-info-panel">
            <view class="task-info-section date-section">
              <view class="info-section-head">
                <text class="info-label">{{ isExecutionDetail ? "本次任务日期" : "任务日期" }}</text>
              </view>
              <text v-if="isExecutionDetail" class="single-date-value">{{ currentDateText }}</text>
              <view v-else class="execution-date-list">
                <button
                  v-for="execution in parentExecutionDates"
                  :key="execution.execution_date_id"
                  class="execution-date-button"
                  :class="getExecutionDisplayClass(execution)"
                  hover-class="button-hover"
                  @tap="goExecutionDetail(execution.execution_date_id)"
                >
                  <text class="execution-date-text">{{ formatTaskDate(execution.execute_date) }}</text>
                  <text class="execution-date-status">{{ getExecutionDisplayLabel(execution) }}</text>
                </button>
              </view>
            </view>
            <view class="task-info-divider" />
            <view class="task-info-section address-section">
              <view class="info-section-head">
                <text class="info-label">地址</text>
                <view class="address-pin" />
              </view>
              <text class="address-title">{{ task.map_point.location_name }}</text>
              <text v-if="task.map_point.location_detail" class="address-detail">
                {{ task.map_point.location_detail }}
              </text>
              <text v-else class="address-detail">暂无详细地址</text>
            </view>
          </view>

          <view v-if="associatedPoi" class="section-card poi-section">
            <view class="section-head">
              <text class="section-title">附近地标</text>
              <button
                class="poi-map-button"
                hover-class="button-hover"
                @tap="goViewAssociatedPoiOnMap"
              >
                地图查看
              </button>
            </view>
            <view class="section-line">
              <text class="section-line-label">名称</text>
              <text class="section-line-value">{{ associatedPoi.name }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">类别</text>
              <text class="section-line-value">
                {{ associatedPoi.category || "腾讯地图点位" }}
              </text>
            </view>
            <view class="section-line">
              <text class="section-line-label">地址</text>
              <text class="section-line-value">{{ associatedPoi.address || "暂无地址" }}</text>
            </view>
          </view>

          <view class="section-card">
            <text class="section-title">任务要求</text>
            <view class="section-line">
              <text class="section-line-label">物资</text>
              <text class="section-line-value">{{ task.required_items }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">说明</text>
              <text class="section-line-value">{{ task.description }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">路线</text>
              <text class="section-line-value">
                {{ task.map_point.route_instruction || "暂无路线说明" }}
              </text>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">任务动态</text>
              <text class="section-meta">{{ activityCountText }}</text>
            </view>
            <view v-if="isExecutionDetail && detailActivities.length" class="timeline">
              <view
                v-for="activity in detailActivities"
                :key="activity.activity_id"
                class="timeline-row"
                :class="{ 'timeline-row-tappable': hasActivityRecord(activity) }"
                @tap="openRecordDetail(activity)"
              >
                <view class="timeline-dot" />
                <view class="timeline-copy">
                  <text class="timeline-title">{{ activity.title }}</text>
                  <text class="timeline-content">{{ activity.content || "暂无备注" }}</text>
                  <text class="timeline-time">{{ formatActivityTime(activity.created_at) }}</text>
                </view>
                <text v-if="hasActivityRecord(activity)" class="timeline-view-link">查看 ›</text>
              </view>
            </view>
            <view v-else-if="!isExecutionDetail && activityExecutionGroups.length" class="execution-groups">
              <view
                v-for="group in activityExecutionGroups"
                :key="group.execution.execution_date_id"
                class="execution-group-card"
              >
                <view class="execution-group-head">
                  <text class="execution-group-date">{{ formatTaskDate(group.execution.execute_date) }}</text>
                  <text class="execution-group-status" :class="getExecutionDisplayClass(group.execution)">
                    {{ getExecutionDisplayLabel(group.execution) }}
                  </text>
                </view>
                <view class="timeline compact-timeline">
                  <view
                    v-for="activity in group.activities"
                    :key="activity.activity_id"
                    class="timeline-row"
                    :class="{ 'timeline-row-tappable': hasActivityRecord(activity) }"
                    @tap="openRecordDetail(activity)"
                  >
                    <view class="timeline-dot" />
                    <view class="timeline-copy">
                      <text class="timeline-title">{{ activity.title }}</text>
                      <text class="timeline-content">{{ activity.content || "暂无备注" }}</text>
                      <text class="timeline-time">{{ formatActivityTime(activity.created_at) }}</text>
                    </view>
                    <text v-if="hasActivityRecord(activity)" class="timeline-view-link">查看 ›</text>
                  </view>
                </view>
              </view>
            </view>
            <text v-else class="empty-line">暂无任务动态</text>
          </view>

        </view>
      </view>
    </scroll-view>

    <view v-if="task" class="bottom-actions">
      <button class="ghost-action" hover-class="button-hover" @tap="goNavigateToTaskPoint">
        导航前往
      </button>
      <button
        class="primary-action"
        :class="`action-${primaryActionState.tone}`"
        :disabled="primaryActionState.disabled"
        hover-class="button-hover"
        @tap="openRecordForm"
      >
        {{ primaryActionState.label }}
      </button>
    </view>

    <view v-if="recordFormVisible" class="modal-mask" @tap="closeRecordForm">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">任务记录</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeRecordForm">×</button>
        </view>
        <text class="modal-hint">
          记录本次投喂情况：上传现场照片，并补充说明（均可选填）。
        </text>
        <view class="record-photo-grid">
          <view
            v-for="(photo, index) in pendingCheckinPhotos"
            :key="`${photo.file_id || photo.file_url}-${index}`"
            class="record-photo-cell"
          >
            <image
              class="record-photo"
              :src="photo.thumbnail_url || photo.file_url"
              mode="aspectFill"
              @tap="openPendingRecordPhotoPreview(photo)"
            />
            <button
              class="record-photo-remove"
              hover-class="button-hover"
              @tap.stop="removeRecordPhoto(photo)"
            >
              ×
            </button>
          </view>
          <button
            v-if="pendingCheckinPhotos.length < 3"
            class="record-photo-upload"
            :loading="isUploading"
            hover-class="button-hover"
            @tap="chooseCheckinPhoto"
          >
            上传图片
          </button>
        </view>
        <textarea
          v-model.trim="recordRemark"
          class="record-remark"
          maxlength="120"
          placeholder="补充说明，可不填"
          placeholder-class="placeholder"
        />
        <button
          class="modal-submit"
          :loading="isSubmitting"
          hover-class="button-hover"
          @tap="submitTaskRecord"
        >
          完成记录
        </button>
      </view>
    </view>

    <view v-if="viewingRecord" class="modal-mask" @tap="closeRecordDetail">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">记录详情</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeRecordDetail">×</button>
        </view>
        <text class="modal-hint">{{ viewingRecordMeta }}</text>
        <text class="modal-record-remark">
          {{ viewingRecord.remark || "暂无补充说明" }}
        </text>
        <view v-if="viewingRecord.photos.length" class="record-photo-grid">
          <image
            v-for="photo in viewingRecord.photos"
            :key="photo.photo_id"
            class="record-photo"
            :src="photo.thumbnail_url || photo.file_url"
            mode="aspectFill"
            @tap="openRecordDetailPhotoPreview(photo)"
          />
        </view>
        <text v-else class="empty-line">本次记录没有照片</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { deleteImageAsset, uploadImage } from "@/api/files";
import {
  checkinTask,
  getTaskDetail,
  type TaskActivityDto,
  type TaskCheckinPhotoDto,
  type TaskCheckinRecordDto,
  type TaskDetailDto,
  type TaskExecutionDto,
  type TaskExecutionGroupDto,
  type UploadedFileRef,
} from "@/api/tasks";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  buildUploadedTaskPhoto,
  formatChinaDateTime,
  formatTaskDate,
  getExecutionDisplayLabel,
  getExecutionDisplayTone,
  getTaskDetailActionState,
  getTaskPhotoDisplayUrl,
} from "@/pages/tasks/task-page";
import { clearTaskListCache } from "@/pages/tasks/task-list-cache";
import { MAP_PENDING_NAVIGATION_STORAGE_KEY } from "@/pages/index/map-page";

import taskIcon from "../../../素材/png/地图点/日常任务.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const taskId = ref("");
const executionDateId = ref("");
const task = ref<TaskDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const isUploading = ref(false);
const isSubmitting = ref(false);
const pendingCheckinPhotos = ref<UploadedFileRef[]>([]);
const failedHeroPhotoIds = ref<string[]>([]);
const recordFormVisible = ref(false);
const recordRemark = ref("");
const viewingRecord = ref<TaskCheckinRecordDto | null>(null);

const heroPhotos = computed(() => {
  if (!task.value) {
    return [];
  }

  const failed = new Set(failedHeroPhotoIds.value);
  return task.value.photos
    .map((photo) => ({
      photo_id: photo.photo_id,
      url: getTaskPhotoDisplayUrl(photo, "task_detail_full"),
    }))
    .filter((photo) => photo.url && !failed.has(photo.photo_id));
});
const isExecutionDetail = computed(() => task.value?.detail_scope === "execution");
const parentExecutionDates = computed<TaskExecutionDto[]>(() =>
  task.value?.display_executions?.length
    ? task.value.display_executions
    : task.value?.execution_dates || [],
);
const currentExecution = computed(
  () => task.value?.execution || task.value?.current_execution || task.value?.next_execution || null,
);
const currentDateText = computed(() => formatTaskDate(currentExecution.value?.execute_date));
const associatedPoi = computed(() => task.value?.map_point.associated_poi || null);
const detailActivities = computed(() => task.value?.activities || []);
const executionGroups = computed<TaskExecutionGroupDto[]>(() => task.value?.execution_groups || []);
const activityExecutionGroups = computed(() =>
  executionGroups.value.filter((group) => group.activities.length),
);
const groupedActivityCount = computed(() =>
  activityExecutionGroups.value.reduce((total, group) => total + group.activities.length, 0),
);
const activityCountText = computed(() => {
  const count = isExecutionDetail.value ? detailActivities.value.length : groupedActivityCount.value;
  return `${count}`;
});
const primaryActionState = computed(() =>
  getTaskDetailActionState({
    task_status: task.value?.status || null,
    can_checkin: Boolean(task.value?.actions.can_checkin && currentExecution.value),
    checkin_disabled_reason: task.value?.actions.checkin_disabled_reason || null,
    current_execution: currentExecution.value
      ? {
          status: currentExecution.value.status,
          display_status: currentExecution.value.display_status,
          execute_date: currentExecution.value.execute_date,
        }
      : null,
  }),
);
const canCheckin = computed(() => !primaryActionState.value.disabled);
const canAdminEditTask = computed(() =>
  Boolean(userStore.isAdmin && task.value?.actions.can_admin_edit),
);
const taskPhotoPreviewUrls = computed(() => heroPhotos.value.map((photo) => photo.url));
const checkinRecords = computed<TaskCheckinRecordDto[]>(() => task.value?.checkins || []);
const viewingRecordMeta = computed(() => {
  if (!viewingRecord.value) {
    return "";
  }
  const nickname = viewingRecord.value.submitter?.nickname || "成员";
  const time = formatActivityTime(viewingRecord.value.submitted_at);
  return time ? `${nickname} · ${time}` : nickname;
});

function findActivityRecord(activity: TaskActivityDto): TaskCheckinRecordDto | null {
  if (activity.activity_type !== "execution_completed") {
    return null;
  }
  const checkinId = activity.metadata?.checkin_id;
  if (typeof checkinId === "string" && checkinId) {
    const byCheckinId = checkinRecords.value.find((record) => record.checkin_id === checkinId);
    if (byCheckinId) {
      return byCheckinId;
    }
  }
  if (activity.task_execution_date_id) {
    return (
      checkinRecords.value.find(
        (record) => record.task_execution_date_id === activity.task_execution_date_id,
      ) || null
    );
  }
  return null;
}

function hasActivityRecord(activity: TaskActivityDto): boolean {
  return findActivityRecord(activity) !== null;
}

function openRecordDetail(activity: TaskActivityDto) {
  const record = findActivityRecord(activity);
  if (record) {
    viewingRecord.value = record;
  }
}

function closeRecordDetail() {
  viewingRecord.value = null;
}

function openRecordDetailPhotoPreview(photo: TaskCheckinPhotoDto) {
  if (!viewingRecord.value) {
    return;
  }
  const urls = viewingRecord.value.photos
    .map((item) => item.file_url || item.thumbnail_url || "")
    .filter((url) => url);
  openImagePreview(urls, photo.file_url || photo.thumbnail_url || "");
}

function getExecutionDisplayClass(execution: TaskExecutionDto): string {
  return `execution-status-${getExecutionDisplayTone(execution)}`;
}

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function formatActivityTime(value: string): string {
  return formatChinaDateTime(value);
}

function markHeroPhotoFailed(photoId: string) {
  if (!failedHeroPhotoIds.value.includes(photoId)) {
    failedHeroPhotoIds.value = [...failedHeroPhotoIds.value, photoId];
  }
}

function openImagePreview(urls: string[], current: string) {
  if (!current) {
    return;
  }
  const uniqueUrls = Array.from(new Set(urls.filter((url) => url)));
  const resolvedUrls = uniqueUrls.includes(current)
    ? uniqueUrls
    : [current, ...uniqueUrls];
  uni.previewImage({
    current,
    urls: resolvedUrls,
  });
}

function openTaskPhotoPreview(photoId: string) {
  const photo = heroPhotos.value.find((item) => item.photo_id === photoId);
  if (!photo) {
    return;
  }
  openImagePreview(taskPhotoPreviewUrls.value, photo.url);
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

async function loadTaskDetail(options: { retry?: boolean } = {}): Promise<void> {
  const token = await getAccessToken();
  if (!token || !taskId.value) {
    return;
  }

  loadState.value = "loading";
  try {
    task.value = await getTaskDetail(token, taskId.value, {
      execution_date_id: executionDateId.value,
    });
    failedHeroPhotoIds.value = [];
    loadState.value = "ready";
  } catch (error) {
    if (options.retry) {
      await wait(350);
      return loadTaskDetail({ retry: false });
    }
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function retryTaskDetail() {
  void loadTaskDetail({ retry: true });
}

function openRecordForm() {
  if (!canCheckin.value) {
    uni.showToast({
      title: task.value?.actions.checkin_disabled_reason || "当前不可记录",
      icon: "none",
    });
    return;
  }
  recordFormVisible.value = true;
}

function closeRecordForm() {
  recordFormVisible.value = false;
}

function chooseCheckinPhoto() {
  if (!canCheckin.value) {
    uni.showToast({
      title: task.value?.actions.checkin_disabled_reason || "当前不可上传",
      icon: "none",
    });
    return;
  }

  const remaining = 3 - pendingCheckinPhotos.value.length;
  if (remaining <= 0) {
    uni.showToast({ title: "最多上传 3 张照片", icon: "none" });
    return;
  }

  uni.chooseImage({
    count: remaining,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths].filter(Boolean);
      void uploadCheckinPhotos(paths.slice(0, remaining));
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
      pendingCheckinPhotos.value = [
        ...pendingCheckinPhotos.value,
        buildUploadedTaskPhoto(asset),
      ];
    }
    uni.showToast({ title: "照片已上传", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploading.value = false;
  }
}

function openPendingRecordPhotoPreview(photo: UploadedFileRef) {
  const urls = pendingCheckinPhotos.value
    .map((item) => item.file_url || item.thumbnail_url || "")
    .filter((url) => url);
  openImagePreview(urls, photo.file_url || photo.thumbnail_url || "");
}

async function removeRecordPhoto(photo: UploadedFileRef) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    if (photo.file_id) {
      await deleteImageAsset(token, photo.file_id);
    }
    pendingCheckinPhotos.value = pendingCheckinPhotos.value.filter((item) => item !== photo);
  } catch (error) {
    const message = error instanceof Error ? error.message : "删除失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

async function submitTaskRecord() {
  const token = await getAccessToken();
  if (!token || !task.value || !currentExecution.value || isSubmitting.value) {
    return;
  }

  if (!canCheckin.value) {
    uni.showToast({
      title: task.value.actions.checkin_disabled_reason || "当前不可记录",
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
      remark: recordRemark.value || null,
      photos: pendingCheckinPhotos.value,
    });
    uni.showToast({ title: "记录已提交", icon: "success" });
    pendingCheckinPhotos.value = [];
    recordRemark.value = "";
    recordFormVisible.value = false;
    clearTaskListCache();
    await loadTaskDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "提交失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function goNavigateToTaskPoint() {
  if (!task.value) {
    return;
  }
  uni.setStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY, {
    source: "task_detail",
    task_id: task.value.task_id,
    map_point_id: task.value.map_point.map_point_id,
    execution_date_id: currentExecution.value?.execution_date_id || null,
    shell_item: {
      id: task.value.task_id,
      map_point_id: task.value.map_point.map_point_id,
      type: "daily_task",
      title: task.value.title,
      subtitle: task.value.map_point.location_name,
      description: task.value.map_point.location_detail,
      distance_meters: null,
      status_label: currentExecution.value
        ? getExecutionDisplayLabel(currentExecution.value)
        : task.value.status_label,
      status_key: currentExecution.value?.display_status || task.value.status,
      tag_label: "投喂任务",
      lng: task.value.map_point.lng,
      lat: task.value.map_point.lat,
      cover_photo_url: task.value.cover_photo_url,
      icon_key: "task_feeding",
      associated_poi: task.value.map_point.associated_poi || null,
      active_execution: currentExecution.value,
    },
  });
  uni.switchTab({ url: "/pages/index/index" });
}

function goViewAssociatedPoiOnMap() {
  const poi = associatedPoi.value;
  if (!poi) {
    return;
  }
  uni.setStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY, {
    source: "task_detail_poi",
    poi,
  });
  uni.switchTab({ url: "/pages/index/index" });
}

function goEditTask() {
  if (!task.value) {
    return;
  }
  const executionQuery = executionDateId.value
    ? `&execution_date_id=${executionDateId.value}`
    : "";
  uni.navigateTo({
    url: `/pages/admin/tasks/create?mode=edit&task_id=${task.value.task_id}${executionQuery}`,
  });
}

function goExecutionDetail(nextExecutionDateId: string) {
  uni.navigateTo({
    url: `/pages/tasks/detail?task_id=${taskId.value}&execution_date_id=${nextExecutionDateId}`,
  });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  taskId.value = typeof query?.task_id === "string" ? query.task_id : "";
  executionDateId.value =
    typeof query?.execution_date_id === "string" ? query.execution_date_id : "";
  void loadTaskDetail({ retry: true });
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
.retry-button::after,
.task-edit-button::after,
.poi-map-button::after,
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
.section-line-label,
.section-line-value,
.section-meta,
.empty-line,
.timeline-title,
.timeline-content,
.timeline-time {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #526070;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
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
  height: 418rpx;
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
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.task-title-row {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 104rpx;
  align-items: center;
  gap: 18rpx;
}

.task-edit-button,
.retry-button {
  margin: 0;
  padding: 0;
  border: 0;
  background: #e8f5e6;
  color: #287c31;
  font-weight: 900;
}

.task-edit-button {
  width: 104rpx;
  height: 56rpx;
  border-radius: 18rpx;
  font-size: 24rpx;
  line-height: 56rpx;
}

.retry-button {
  width: 168rpx;
  height: 64rpx;
  margin-top: 22rpx;
  border-radius: 20rpx;
  font-size: 25rpx;
  line-height: 64rpx;
}

.task-desc {
  margin-top: 18rpx;
  color: #465160;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
}

.task-info-panel,
.section-card,
.state-box {
  box-sizing: border-box;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.task-info-panel {
  margin-top: 34rpx;
  overflow: hidden;
  border: 2rpx solid rgba(212, 237, 208, 0.72);
}

.task-info-section {
  padding: 28rpx;
}

.date-section {
  background: rgba(247, 252, 246, 0.78);
}

.address-section {
  background: rgba(255, 255, 255, 0.68);
}

.task-info-divider {
  height: 1rpx;
  margin: 0 28rpx;
  background: rgba(189, 214, 185, 0.72);
}

.info-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.single-date-value,
.address-title,
.address-detail {
  display: block;
}

.single-date-value {
  margin-top: 18rpx;
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.address-title {
  margin-top: 18rpx;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.35;
}

.address-detail {
  margin-top: 10rpx;
  color: #4b5563;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.5;
}

.address-pin {
  position: relative;
  width: 26rpx;
  height: 26rpx;
  border: 5rpx solid #63b95d;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: #ffffff;
}

.address-pin::after {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #63b95d;
  content: "";
  transform: translate(-50%, -50%);
}

.execution-date-list {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.execution-date-button,
.execution-group-status {
  border: 0;
  border-radius: 16rpx;
  font-weight: 900;
}

.execution-date-button {
  min-width: 160rpx;
  height: 68rpx;
  margin: 0;
  padding: 8rpx 16rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5rpx;
}

.execution-date-button::after {
  border: 0;
}

.execution-date-text,
.execution-date-status {
  display: block;
  overflow: hidden;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.execution-date-text {
  font-size: 22rpx;
}

.execution-date-status {
  font-size: 18rpx;
}

.execution-status-not_started {
  background: #ffe7eb;
  color: #d73546;
}

.execution-status-in_progress {
  background: #fff4cc;
  color: #a66f00;
}

.execution-status-completed {
  background: #e6f6e4;
  color: #238033;
}

.execution-status-cancelled {
  background: #e5e7eb;
  color: #667085;
}

.execution-status-default {
  background: #edf4ff;
  color: #2276ff;
}

.info-label,
.section-meta,
.empty-line,
.timeline-time {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
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

.poi-map-button {
  width: 126rpx;
  height: 56rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #e9f7e9;
  color: #287c31;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 56rpx;
}

.section-line {
  margin-top: 16rpx;
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  line-height: 1.55;
}

.section-line-label {
  flex: 0 0 70rpx;
  color: #788293;
  font-size: 24rpx;
  font-weight: 800;
}

.section-line-value {
  flex: 1;
  min-width: 0;
  color: #273040;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.55;
}

.timeline {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.section-card > .timeline {
  max-height: 520rpx;
  overflow-y: auto;
}

.execution-groups {
  margin-top: 22rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  max-height: 620rpx;
  overflow-y: auto;
}

.execution-group-card {
  box-sizing: border-box;
  border: 2rpx solid rgba(197, 230, 193, 0.72);
  border-radius: 22rpx;
  padding: 20rpx;
  background: rgba(247, 252, 246, 0.72);
}

.execution-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.execution-group-date {
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.execution-group-status {
  padding: 8rpx 14rpx;
  font-size: 20rpx;
}

.compact-timeline {
  margin-top: 18rpx;
  gap: 18rpx;
}

.timeline-row {
  display: grid;
  grid-template-columns: 24rpx minmax(0, 1fr);
  gap: 18rpx;
}

.timeline-row-tappable {
  grid-template-columns: 24rpx minmax(0, 1fr) auto;
  align-items: center;
}

.timeline-view-link {
  color: #2f8037;
  font-size: 24rpx;
  font-weight: 900;
  white-space: nowrap;
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

.photo-strip {
  margin-top: 22rpx;
  display: flex;
  gap: 14rpx;
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
  max-height: 148rpx;
}

.checkin-photo-cell {
  position: relative;
  flex: 0 0 126rpx;
  width: 126rpx;
  height: 126rpx;
}

.checkin-photo {
  width: 126rpx;
  height: 126rpx;
  border-radius: 20rpx;
}

.photo-delete-button {
  position: absolute;
  right: 6rpx;
  top: 6rpx;
  width: 58rpx;
  height: 36rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: rgba(215, 53, 70, 0.92);
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 36rpx;
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

.primary-action.action-ready {
  background: #287c31;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.primary-action.action-not_started,
.primary-action.action-not_started[disabled] {
  background: #d73546;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(215, 53, 70, 0.18);
}

.primary-action.action-completed,
.primary-action.action-completed[disabled] {
  background: #9ca3af;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(75, 85, 99, 0.14);
}

.primary-action.action-cancelled,
.primary-action.action-cancelled[disabled] {
  background: #9ca3af;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(75, 85, 99, 0.14);
}

.primary-action.action-archived,
.primary-action.action-archived[disabled] {
  background: #9ca3af;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(75, 85, 99, 0.14);
}

.primary-action[disabled] {
  opacity: 1;
}

.modal-mask {
  position: fixed;
  z-index: 20;
  inset: 0;
  background: rgba(17, 24, 39, 0.46);
  display: flex;
  align-items: flex-end;
  animation: modal-mask-fade 200ms ease-out;
}

.modal-panel {
  box-sizing: border-box;
  width: 100%;
  max-height: 82vh;
  padding: 30rpx 32rpx calc(env(safe-area-inset-bottom) + 32rpx);
  border-radius: 36rpx 36rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -18rpx 46rpx rgba(42, 63, 43, 0.18);
  animation: modal-panel-rise 240ms cubic-bezier(0.22, 1, 0.36, 1);
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.modal-title {
  color: #171b22;
  font-size: 34rpx;
  font-weight: 900;
}

.modal-close::after,
.record-photo-upload::after,
.record-photo-remove::after,
.modal-submit::after {
  border: 0;
}

.modal-close {
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #eef2ee;
  color: #526070;
  font-size: 36rpx;
  line-height: 54rpx;
}

.modal-hint {
  display: block;
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.45;
}

.record-photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  margin-top: 24rpx;
}

.record-photo-cell {
  position: relative;
}

.record-photo {
  display: block;
  width: 190rpx;
  height: 190rpx;
  border-radius: 24rpx;
  background: #f1f5f0;
  box-shadow: 0 8rpx 22rpx rgba(42, 63, 43, 0.12);
}

.record-photo-remove {
  position: absolute;
  top: -14rpx;
  right: -14rpx;
  width: 44rpx;
  height: 44rpx;
  margin: 0;
  padding: 0;
  border: 4rpx solid #ffffff;
  border-radius: 50%;
  background: #3c4553;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 36rpx;
}

.record-photo-upload {
  width: 190rpx;
  height: 190rpx;
  margin: 0;
  padding: 0;
  border: 2rpx dashed rgba(47, 128, 55, 0.5);
  border-radius: 24rpx;
  background: #f4fbef;
  color: #2f8037;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 186rpx;
}

.record-remark {
  box-sizing: border-box;
  width: 100%;
  min-height: 150rpx;
  margin-top: 24rpx;
  padding: 22rpx;
  border: 2rpx solid rgba(47, 128, 55, 0.24);
  border-radius: 22rpx;
  background: #fcfefb;
  color: #171b22;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
}

.placeholder {
  color: #8b919b;
}

.modal-submit {
  width: 100%;
  height: 86rpx;
  margin: 28rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 86rpx;
  box-shadow: 0 14rpx 34rpx rgba(47, 128, 55, 0.24);
}

.modal-record-remark {
  display: block;
  margin-top: 20rpx;
  padding: 20rpx 22rpx;
  border-radius: 20rpx;
  background: #f4fbef;
  color: #273040;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.55;
}

@keyframes modal-mask-fade {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes modal-panel-rise {
  from {
    opacity: 0.6;
    transform: translateY(64rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
