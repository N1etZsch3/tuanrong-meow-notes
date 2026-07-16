<template>
  <view class="publish-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="publish-scroll" scroll-y :show-scrollbar="false">
      <view class="publish-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">{{ pageTitle }}</text>
            <text class="nav-subtitle">{{ pageSubtitle }}</text>
          </view>
        </view>

        <view v-if="isLoadingDetail" class="form-section loading-section">
          <text class="loading-title">正在加载地标点数据...</text>
        </view>

        <view class="type-chip">
          <image class="chip-icon" :src="landmarkIcon" mode="aspectFit" />
          <text>地标点</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">1</text>
            <text class="section-title">地标名称</text>
          </view>
          <textarea
            v-model.trim="form.name"
            class="field-textarea title-textarea"
            maxlength="30"
            placeholder="请输入地标名称"
            placeholder-class="placeholder"
          />
          <text class="char-count">{{ form.name.length }}/30</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">2</text>
            <text class="section-title">地标位置</text>
          </view>
          <view class="location-layout">
            <view class="map-preview">
              <text class="map-label">{{ selectedLocation?.location_name || "未选择位置" }}</text>
              <view class="map-pin">●</view>
            </view>
            <view class="location-copy">
              <text class="location-title">
                {{ selectedLocation?.location_name || "请选择地标位置" }}
              </text>
              <text class="location-detail">
                {{ selectedLocation?.location_detail || "点击地图选点，位置名称会使用地标名称" }}
              </text>
              <text v-if="selectedLocation?.tencent_poi_name" class="location-detail">
                附近地标：{{ selectedLocation.tencent_poi_name }}
              </text>
              <button class="outline-button" hover-class="button-hover" @tap="goLocation">
                地图选点
              </button>
            </view>
          </view>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">3</text>
            <text class="section-title">照片</text>
          </view>
          <SortableImageGrid
            :images="landmarkPhotoItems"
            :uploading="isUploading"
            @add="choosePhoto"
            @remove="removePhotoAt"
            @reorder="reorderPhoto"
          />
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">4</text>
            <text class="section-title">地标说明</text>
          </view>
          <textarea
            v-model.trim="form.description"
            class="field-textarea"
            maxlength="180"
            placeholder="说明地标特征、到达方式或路线提示"
            placeholder-class="placeholder"
          />
        </view>
      </view>
    </scroll-view>

    <view class="bottom-actions" :class="{ 'is-edit': isEditMode }">
      <button
        v-if="isEditMode"
        class="delete-button"
        :disabled="isSubmitting || isLoadingDetail"
        hover-class="button-hover"
        @tap="confirmDelete"
      >
        删除
      </button>
      <button class="cancel-button" hover-class="button-hover" @tap="goBack">取消</button>
      <button
        class="submit-button"
        :loading="isSubmitting"
        :disabled="isLoadingDetail"
        hover-class="button-hover"
        @tap="submitLandmark"
      >
        {{ submitButtonText }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad, onShow } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";

import { uploadImage } from "@/api/files";
import {
  createLandmark,
  deleteLandmark,
  getAdminLandmarkDetail,
  updateLandmark,
  type LandmarkPhotoPayload,
} from "@/api/landmarks";
import SortableImageGrid from "@/components/SortableImageGrid.vue";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import { moveArrayItem } from "@/utils/array-order";
import { returnToListAfterDelete } from "@/utils/delete-navigation";
import { completeCreateOrEditNavigation } from "@/utils/save-navigation";
import {
  HBNU_DEFAULT_LANDMARK_LOCATION,
  LANDMARK_LOCATION_STORAGE_KEY,
  buildLandmarkPayload,
  buildUploadedLandmarkPhoto,
  createDefaultLandmarkDraft,
  detailToDraft,
  validateLandmarkDraft,
  type LandmarkDraft,
  type SelectedLandmarkLocation,
} from "@/pages/admin/landmarks/landmark-page";

import landmarkIcon from "../../../../素材/png/地图点/地标.png";
import loadingBackground from "../../../../素材/加载页素材/背景.jpg";

const userStore = useUserStore();
const form = reactive<LandmarkDraft>(createDefaultLandmarkDraft());
const editLandmarkId = ref("");
const isUploading = ref(false);
const isSubmitting = ref(false);
const isLoadingDetail = ref(false);
const isEditMode = computed(() => Boolean(editLandmarkId.value));
const pageTitle = computed(() => (isEditMode.value ? "编辑地标点" : "新建地标点"));
const pageSubtitle = computed(() =>
  isEditMode.value ? "修改地标位置、照片和说明" : "创建地图上的长期地标点",
);
const submitButtonText = computed(() => (isEditMode.value ? "保存修改" : "发布地标点"));
const selectedLocation = computed(() => form.location);
const landmarkPhotoItems = computed(() =>
  form.photos.map((photo) => ({
    key: photo.file_id || photo.file_url,
    url: photo.thumbnail_url || photo.file_url,
  })),
);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function removePhoto(photo: LandmarkPhotoPayload) {
  form.photos = form.photos.filter((item) => item !== photo);
}

function removePhotoAt(index: number) {
  const photo = form.photos[index];
  if (photo) {
    removePhoto(photo);
  }
}

function reorderPhoto(fromIndex: number, toIndex: number) {
  form.photos = moveArrayItem(form.photos, fromIndex, toIndex);
}

function choosePhoto() {
  uni.chooseImage({
    count: 3,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths].filter(Boolean);
      void uploadPhotos(paths);
    },
  });
}

async function uploadPhotos(paths: string[]) {
  const token = await getAccessToken();
  if (!token || !paths.length) {
    return;
  }
  isUploading.value = true;
  try {
    for (const path of paths) {
      const asset = await uploadImage(token, path, {
        usage_type: "map_point_scene",
        owner_type: "map_point",
        visibility: "internal",
        caption: "地标照片",
      });
      form.photos = [...form.photos, buildUploadedLandmarkPhoto(asset)];
    }
    uni.showToast({ title: "图片已上传", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploading.value = false;
  }
}

function ensureLocationDraftForPicker() {
  const location = form.location || { ...HBNU_DEFAULT_LANDMARK_LOCATION };
  const nextLocation: SelectedLandmarkLocation = {
    ...location,
    location_name: form.name.trim(),
    route_instruction: form.description || location.route_instruction || "",
  };
  uni.setStorageSync(LANDMARK_LOCATION_STORAGE_KEY, nextLocation);
}

function goLocation() {
  if (!form.name.trim()) {
    uni.showToast({ title: "请先填写地标名称", icon: "none" });
    return;
  }
  ensureLocationDraftForPicker();
  uni.navigateTo({ url: "/pages/admin/landmarks/location" });
}

async function submitLandmark() {
  const validation = validateLandmarkDraft(form);
  if (!validation.valid) {
    uni.showToast({ title: validation.message || "请完善地标点信息", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token || isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  try {
    const payload = buildLandmarkPayload(form);
    const response = isEditMode.value
      ? await updateLandmark(token, editLandmarkId.value, payload)
      : await createLandmark(token, payload);
    const landmarkId = isEditMode.value ? editLandmarkId.value : response.landmark_id;
    uni.removeStorageSync(LANDMARK_LOCATION_STORAGE_KEY);
    uni.showToast({ title: isEditMode.value ? "地标点已保存" : "地标点已发布", icon: "success" });
    completeCreateOrEditNavigation({
      isEditMode: isEditMode.value,
      detailUrl: `/pages/landmarks/detail?landmark_id=${landmarkId}`,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "提交失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function confirmDelete() {
  if (!isEditMode.value || isSubmitting.value) {
    return;
  }
  uni.showModal({
    title: "删除地标点",
    content: "删除后地图上将不再显示该地标点。",
    confirmText: "删除",
    confirmColor: "#d14343",
    success: (result) => {
      if (result.confirm) {
        void deleteCurrentLandmark();
      }
    },
  });
}

async function deleteCurrentLandmark() {
  const token = await getAccessToken();
  if (!token || !editLandmarkId.value) {
    return;
  }
  isSubmitting.value = true;
  try {
    await deleteLandmark(token, editLandmarkId.value);
    uni.removeStorageSync(LANDMARK_LOCATION_STORAGE_KEY);
    uni.showToast({ title: "地标点已删除", icon: "success" });
    returnToListAfterDelete("/pages/landmarks/index");
  } catch (error) {
    const message = error instanceof Error ? error.message : "删除失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function applyDetailToForm(detail: Awaited<ReturnType<typeof getAdminLandmarkDetail>>) {
  const draft = detailToDraft(detail);
  form.name = draft.name;
  form.description = draft.description;
  form.location = draft.location;
  form.photos = draft.photos;
}

async function loadEditableDetail() {
  const token = await getAccessToken();
  if (!token || !editLandmarkId.value) {
    return;
  }
  isLoadingDetail.value = true;
  try {
    applyDetailToForm(await getAdminLandmarkDetail(token, editLandmarkId.value));
  } catch (error) {
    const message = error instanceof Error ? error.message : "地标点数据加载失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isLoadingDetail.value = false;
  }
}

function readSelectedLocation() {
  const value = uni.getStorageSync(LANDMARK_LOCATION_STORAGE_KEY);
  if (value && typeof value === "object") {
    const location = value as SelectedLandmarkLocation;
    form.location = {
      ...location,
      location_name: form.name.trim() || location.location_name,
    };
    uni.removeStorageSync(LANDMARK_LOCATION_STORAGE_KEY);
  }
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  readSelectedLocation();
});

onLoad((query) => {
  editLandmarkId.value =
    typeof query?.landmark_id === "string" ? query.landmark_id : "";
  if (editLandmarkId.value) {
    void loadEditableDetail();
  }
});
</script>

<style scoped>
.publish-page {
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

.publish-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.publish-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 166rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button,
.outline-button,
.photo-remove,
.photo-upload,
.delete-button,
.cancel-button,
.submit-button {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.outline-button::after,
.photo-remove::after,
.photo-upload::after,
.delete-button::after,
.cancel-button::after,
.submit-button::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.section-title,
.char-count,
.location-title,
.location-detail,
.loading-title {
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
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.type-chip {
  width: fit-content;
  margin-top: 34rpx;
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: #e8f5e6;
  color: #287c31;
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 25rpx;
  font-weight: 900;
}

.chip-icon {
  width: 36rpx;
  height: 36rpx;
}

.form-section {
  position: relative;
  box-sizing: border-box;
  margin-top: 28rpx;
  padding: 30rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.loading-section {
  padding: 26rpx 30rpx;
}

.loading-title {
  color: #287c31;
  font-size: 26rpx;
  font-weight: 900;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.step-badge {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #287c31;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 40rpx;
  text-align: center;
}

.section-title {
  color: #111827;
  font-size: 31rpx;
  font-weight: 900;
}

.field-textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 160rpx;
  margin-top: 24rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.35);
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #111827;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.5;
  padding: 24rpx;
}

.title-textarea {
  min-height: 150rpx;
}

.placeholder {
  color: #8b919b;
  font-weight: 700;
}

.char-count {
  margin-top: 10rpx;
  color: #6b7280;
  font-size: 22rpx;
  text-align: right;
}

.location-layout {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: 250rpx minmax(0, 1fr);
  gap: 24rpx;
  align-items: center;
}

.map-preview {
  position: relative;
  height: 220rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.68) 11rpx, transparent 1rpx),
    linear-gradient(rgba(255, 255, 255, 0.68) 11rpx, transparent 1rpx),
    #dff2d2;
  background-size: 58rpx 58rpx;
}

.map-label {
  position: absolute;
  left: 18rpx;
  right: 18rpx;
  bottom: 18rpx;
  padding: 8rpx 10rpx;
  border-radius: 12rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #2f3a2f;
  font-size: 22rpx;
  font-weight: 900;
  text-align: center;
}

.map-pin {
  position: absolute;
  left: 50%;
  top: 44%;
  width: 68rpx;
  height: 68rpx;
  margin: -34rpx 0 0 -34rpx;
  border-radius: 50%;
  background: #287c31;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 68rpx;
  text-align: center;
  box-shadow: 0 0 0 24rpx rgba(40, 124, 49, 0.16);
}

.location-title {
  color: #111827;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.35;
}

.location-detail {
  margin-top: 14rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.45;
}

.outline-button {
  width: 174rpx;
  height: 68rpx;
  margin-top: 22rpx;
  border: 2rpx solid #287c31;
  border-radius: 20rpx;
  background: #ffffff;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 64rpx;
}

.photo-grid {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.photo-item,
.photo-thumb,
.photo-upload {
  width: 150rpx;
  height: 150rpx;
  border-radius: 22rpx;
}

.photo-item {
  position: relative;
}

.photo-thumb {
  overflow: hidden;
}

.photo-remove {
  position: absolute;
  top: -14rpx;
  right: -14rpx;
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  background: rgba(17, 24, 39, 0.72);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 42rpx;
}

.photo-upload {
  border: 2rpx dashed rgba(40, 124, 49, 0.5);
  background: #f4fbef;
  color: #287c31;
  font-size: 58rpx;
  font-weight: 700;
  line-height: 138rpx;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22rpx;
}

.bottom-actions.is-edit {
  grid-template-columns: 150rpx minmax(0, 1fr) minmax(0, 1fr);
}

.delete-button,
.cancel-button,
.submit-button {
  height: 92rpx;
  border-radius: 30rpx;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 92rpx;
}

.delete-button {
  border: 2rpx solid #d14343;
  background: rgba(255, 255, 255, 0.96);
  color: #d14343;
}

.cancel-button {
  border: 2rpx solid #287c31;
  background: rgba(255, 255, 255, 0.96);
  color: #287c31;
}

.submit-button {
  background: #287c31;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.22);
}

.submit-button[disabled] {
  background: #9fb59d;
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
