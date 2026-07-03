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
          <text class="loading-title">正在加载物资点数据...</text>
        </view>

        <view class="type-chip">
          <image class="chip-icon" :src="supplyIcon" mode="aspectFit" />
          <text>物资点</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">1</text>
            <text class="section-title">物资点名称</text>
          </view>
          <textarea
            v-model.trim="form.name"
            class="field-textarea title-textarea"
            maxlength="30"
            placeholder="请输入物资点名称"
            placeholder-class="placeholder"
          />
          <text class="char-count">{{ form.name.length }}/30</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">2</text>
            <text class="section-title">物资点位置</text>
          </view>
          <view class="location-layout">
            <view class="map-preview">
              <text class="map-label">{{ selectedLocation?.location_name || "未选择位置" }}</text>
              <view class="map-pin">●</view>
            </view>
            <view class="location-copy">
              <text class="location-title">
                {{ selectedLocation?.location_name || "请选择物资点位置" }}
              </text>
              <text class="location-detail">
                {{ selectedLocation?.location_detail || "点击地图选点，位置名称会使用物资点名称" }}
              </text>
              <text v-if="selectedLocation?.tencent_poi_name" class="location-detail">
                公共地点：{{ selectedLocation.tencent_poi_name }}
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
            <text class="section-title">物资类型和数量</text>
          </view>
          <text class="section-hint">系统物资可直接添加，自定义物资仅显示文字标签。</text>
          <view class="system-chip-grid">
            <button
              v-for="item in systemItems"
              :key="item.local_id"
              class="supply-chip"
              :class="`chip-${item.color_key}`"
              hover-class="button-hover"
              @tap="addSystemItem(item)"
            >
              <image
                v-if="getSupplyItemIcon(item.icon_key)"
                class="supply-chip-icon"
                :src="getSupplyItemIcon(item.icon_key)"
                mode="aspectFit"
              />
              <text>{{ item.item_name }}</text>
            </button>
          </view>

          <view class="custom-row">
            <input
              v-model.trim="customItemName"
              class="field-input custom-input"
              maxlength="12"
              placeholder="自定义物资"
              placeholder-class="placeholder"
            />
            <button class="add-custom-button" hover-class="button-hover" @tap="addCustomItem">
              添加
            </button>
          </view>

          <view v-if="form.items.length" class="selected-items">
            <view
              v-for="item in form.items"
              :key="item.local_id"
              class="selected-item"
              :class="`item-${item.color_key}`"
            >
              <view class="selected-item-main">
                <view class="selected-item-title">
                  <image
                    v-if="getSupplyItemIcon(item.icon_key)"
                    class="selected-item-icon"
                    :src="getSupplyItemIcon(item.icon_key)"
                    mode="aspectFit"
                  />
                  <text class="selected-item-name">{{ item.item_name }}</text>
                </view>
                <text class="selected-item-label">{{ supplyItemLabel(item) }}</text>
              </view>
              <view class="quantity-control">
                <button class="quantity-button" hover-class="button-hover" @tap="changeQuantity(item.local_id, -1)">
                  -
                </button>
                <input
                  v-model.number="item.quantity"
                  class="quantity-input"
                  type="number"
                />
                <button class="quantity-button" hover-class="button-hover" @tap="changeQuantity(item.local_id, 1)">
                  +
                </button>
              </view>
              <button class="remove-item" hover-class="button-hover" @tap="removeItem(item.local_id)">
                删除
              </button>
            </view>
          </view>
          <text v-else class="empty-line">尚未添加物资</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">4</text>
            <text class="section-title">物资点照片</text>
          </view>
          <view class="photo-grid">
            <view
              v-for="photo in form.photos"
              :key="photo.file_id || photo.file_url"
              class="photo-item"
            >
              <image class="photo-thumb" :src="photo.thumbnail_url || photo.file_url" mode="aspectFill" />
              <button class="photo-remove" hover-class="button-hover" @tap="removePhoto(photo)">
                ×
              </button>
            </view>
            <button
              class="photo-upload"
              :loading="isUploading"
              hover-class="button-hover"
              @tap="choosePhoto"
            >
              +
            </button>
          </view>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">5</text>
            <text class="section-title">路线说明</text>
          </view>
          <textarea
            v-model.trim="form.route_instruction"
            class="field-textarea"
            maxlength="120"
            placeholder="例如：从宿舍背后小路进入，靠近 A-3 楼梯间"
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
        @tap="submitSupplyPoint"
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
  createSupplyPoint,
  deleteSupplyPoint,
  getAdminSupplyPointDetail,
  updateSupplyPoint,
  type SupplyItemDto,
  type SupplyPointDetailDto,
  type UploadedFileRef,
} from "@/api/supplies";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import {
  HBNU_DEFAULT_SUPPLY_LOCATION,
  SUPPLY_LOCATION_STORAGE_KEY,
  SYSTEM_SUPPLY_ITEMS,
  buildCustomSupplyItem,
  buildSupplyPayload,
  buildUploadedSupplyPhoto,
  cloneSystemSupplyItem,
  createDefaultSupplyDraft,
  dtoItemToDraftItem,
  supplyItemLabel,
  supplyPhotoToUploadedRef,
  validateSupplyDraft,
  type SelectedSupplyLocation,
  type SupplyDraftItem,
  type SupplyPointDraft,
} from "@/pages/admin/supplies/supply-page";

import supplyIcon from "../../../../素材/icon/物资.png";
import carrierIcon from "../../../../素材/svg/物资点/航空箱.svg";
import catFoodIcon from "../../../../素材/svg/物资点/猫粮.svg";
import glovesIcon from "../../../../素材/svg/物资点/手套.svg";
import netIcon from "../../../../素材/svg/物资点/网兜.svg";
import trapIcon from "../../../../素材/svg/物资点/诱捕笼.svg";
import waterIcon from "../../../../素材/svg/物资点/水.svg";
import loadingBackground from "../../../../素材/加载页素材/加载页背景.jpg";

const userStore = useUserStore();
const form = reactive<SupplyPointDraft>(createDefaultSupplyDraft());
const editSupplyPointId = ref("");
const isUploading = ref(false);
const isSubmitting = ref(false);
const isLoadingDetail = ref(false);
const customItemName = ref("");
const systemItems = SYSTEM_SUPPLY_ITEMS;
const supplyItemIcons: Record<string, string> = {
  carrier: carrierIcon,
  cat_food: catFoodIcon,
  gloves: glovesIcon,
  net: netIcon,
  trap: trapIcon,
  water: waterIcon,
};
const isEditMode = computed(() => Boolean(editSupplyPointId.value));
const pageTitle = computed(() => (isEditMode.value ? "编辑物资点" : "新建物资点"));
const pageSubtitle = computed(() =>
  isEditMode.value ? "修改物资点位置、物资和照片" : "创建地图上的长期物资点",
);
const submitButtonText = computed(() => (isEditMode.value ? "保存修改" : "发布物资点"));
const selectedLocation = computed(() => form.location);

function getSupplyItemIcon(iconKey?: string | null): string {
  return iconKey ? supplyItemIcons[iconKey] || "" : "";
}

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function addSystemItem(item: SupplyDraftItem) {
  const existing = form.items.find((current) => current.item_type === item.item_type);
  if (existing) {
    existing.quantity += 1;
    return;
  }
  form.items = [...form.items, cloneSystemSupplyItem(item)];
}

function addCustomItem() {
  const name = customItemName.value.trim();
  if (!name) {
    uni.showToast({ title: "请输入自定义物资名称", icon: "none" });
    return;
  }
  form.items = [...form.items, buildCustomSupplyItem(name)];
  customItemName.value = "";
}

function changeQuantity(localId: string, delta: number) {
  const item = form.items.find((current) => current.local_id === localId);
  if (!item) {
    return;
  }
  item.quantity = Math.max(0, Number(item.quantity || 0) + delta);
}

function removeItem(localId: string) {
  form.items = form.items.filter((item) => item.local_id !== localId);
}

function removePhoto(photo: UploadedFileRef) {
  form.photos = form.photos.filter((item) => item !== photo);
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
        owner_type: "supply_point",
        visibility: "internal",
        caption: "物资点照片",
      });
      form.photos = [...form.photos, buildUploadedSupplyPhoto(asset)];
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
  const location = form.location || { ...HBNU_DEFAULT_SUPPLY_LOCATION };
  const nextLocation: SelectedSupplyLocation = {
    ...location,
    location_name: form.name.trim(),
    route_instruction: form.route_instruction || location.route_instruction || "",
  };
  uni.setStorageSync(SUPPLY_LOCATION_STORAGE_KEY, nextLocation);
}

function goLocation() {
  if (!form.name.trim()) {
    uni.showToast({ title: "请先填写物资点名称", icon: "none" });
    return;
  }
  ensureLocationDraftForPicker();
  const suffix = isEditMode.value
    ? `?mode=edit&supply_point_id=${editSupplyPointId.value}`
    : "";
  uni.navigateTo({ url: `/pages/admin/supplies/location${suffix}` });
}

async function submitSupplyPoint() {
  const validation = validateSupplyDraft(form);
  if (!validation.valid) {
    uni.showToast({ title: validation.message || "请完善物资点信息", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token || isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  try {
    const payload = buildSupplyPayload(form);
    const response = isEditMode.value
      ? await updateSupplyPoint(token, editSupplyPointId.value, payload)
      : await createSupplyPoint(payload, token);
    const supplyPointId = isEditMode.value
      ? editSupplyPointId.value
      : response.supply_point_id;
    uni.removeStorageSync(SUPPLY_LOCATION_STORAGE_KEY);
    uni.showToast({ title: isEditMode.value ? "物资点已保存" : "物资点已发布", icon: "success" });
    uni.redirectTo({ url: `/pages/supplies/detail?supply_point_id=${supplyPointId}` });
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
    title: "删除物资点",
    content: "删除后地图上将不再显示该物资点，历史记录会保留在数据库中。",
    confirmText: "删除",
    confirmColor: "#d14343",
    success: (result) => {
      if (result.confirm) {
        void deleteCurrentSupplyPoint();
      }
    },
  });
}

async function deleteCurrentSupplyPoint() {
  const token = await getAccessToken();
  if (!token || !editSupplyPointId.value) {
    return;
  }
  isSubmitting.value = true;
  try {
    await deleteSupplyPoint(token, editSupplyPointId.value);
    uni.removeStorageSync(SUPPLY_LOCATION_STORAGE_KEY);
    uni.showToast({ title: "物资点已删除", icon: "success" });
    uni.switchTab({ url: "/pages/index/index" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "删除失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function applyDetailToForm(detail: SupplyPointDetailDto) {
  form.name = detail.name || "";
  form.description = detail.description || "";
  form.items = detail.initial_items.map((item: SupplyItemDto) => dtoItemToDraftItem(item));
  form.location = {
    campus_id: detail.map_point.campus_id,
    area_id: detail.map_point.area_id,
    location_name: detail.name,
    location_detail: detail.map_point.location_detail,
    lng: detail.map_point.lng,
    lat: detail.map_point.lat,
    route_instruction: detail.map_point.route_instruction,
    landmark_hint: detail.map_point.landmark_hint,
    entrance_hint: detail.map_point.entrance_hint,
    amap_poi_id: detail.map_point.amap_poi_id,
    amap_address: detail.map_point.amap_address,
    tencent_poi_id: detail.map_point.tencent_poi_id,
    tencent_poi_name: detail.map_point.tencent_poi_name,
    tencent_poi_address: detail.map_point.tencent_poi_address,
    tencent_poi_category: detail.map_point.tencent_poi_category,
    tencent_poi_lng: detail.map_point.tencent_poi_lng,
    tencent_poi_lat: detail.map_point.tencent_poi_lat,
    tencent_poi_distance_meters: detail.map_point.tencent_poi_distance_meters,
    tencent_poi_match_method: detail.map_point.tencent_poi_match_method,
  };
  form.route_instruction = detail.map_point.route_instruction || detail.access_instruction || "";
  form.photos = detail.photos.map(supplyPhotoToUploadedRef);
}

async function loadEditableDetail() {
  const token = await getAccessToken();
  if (!token || !editSupplyPointId.value) {
    return;
  }
  isLoadingDetail.value = true;
  try {
    const detail = await getAdminSupplyPointDetail(token, editSupplyPointId.value);
    applyDetailToForm(detail);
  } catch (error) {
    const message = error instanceof Error ? error.message : "物资点数据加载失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isLoadingDetail.value = false;
  }
}

function readSelectedLocation() {
  const value = uni.getStorageSync(SUPPLY_LOCATION_STORAGE_KEY);
  if (value && typeof value === "object") {
    const location = value as SelectedSupplyLocation;
    form.location = {
      ...location,
      location_name: form.name.trim() || location.location_name,
    };
    form.route_instruction = location.route_instruction || form.route_instruction;
  }
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  readSelectedLocation();
});

onLoad((query) => {
  editSupplyPointId.value =
    typeof query?.supply_point_id === "string" ? query.supply_point_id : "";
  if (editSupplyPointId.value) {
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

.back-button {
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
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
.submit-button::after,
.supply-chip::after,
.add-custom-button::after,
.quantity-button::after,
.remove-item::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.section-title,
.section-hint,
.char-count,
.location-title,
.location-detail,
.empty-line {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: 46rpx;
  font-weight: 900;
}

.nav-subtitle {
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 25rpx;
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
  display: block;
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

.section-hint {
  margin: 12rpx 0 22rpx 54rpx;
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 700;
}

.field-textarea,
.field-input {
  box-sizing: border-box;
  width: 100%;
  margin-top: 24rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.35);
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #111827;
  font-size: 27rpx;
  font-weight: 700;
}

.field-textarea {
  min-height: 160rpx;
  padding: 24rpx;
  line-height: 1.5;
}

.title-textarea {
  min-height: 150rpx;
}

.field-input {
  height: 82rpx;
  padding: 0 24rpx;
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
  margin: 22rpx 0 0;
  padding: 0;
  border: 2rpx solid #287c31;
  border-radius: 20rpx;
  background: #ffffff;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 64rpx;
}

.system-chip-grid,
.selected-items,
.photo-grid {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.supply-chip {
  height: 58rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.supply-chip-icon,
.selected-item-icon {
  width: 30rpx;
  height: 30rpx;
}

.chip-green,
.item-green {
  background: #e4f6dd;
  color: #237a2f;
}

.chip-blue,
.item-blue {
  background: #dff1ff;
  color: #1d6fb8;
}

.chip-purple,
.item-purple {
  background: #efe8ff;
  color: #6d42b8;
}

.chip-teal,
.item-teal {
  background: #def7f0;
  color: #167766;
}

.chip-orange,
.item-orange {
  background: #fff0d9;
  color: #a45b00;
}

.chip-red,
.item-red {
  background: #ffe6e6;
  color: #c43b3b;
}

.chip-gray,
.item-gray {
  background: #edf0f3;
  color: #526070;
}

.custom-row {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 128rpx;
  gap: 14rpx;
}

.custom-input {
  margin-top: 0;
}

.add-custom-button {
  height: 82rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 22rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 82rpx;
}

.selected-items {
  flex-direction: column;
}

.selected-item {
  box-sizing: border-box;
  padding: 18rpx;
  border-radius: 22rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 190rpx 76rpx;
  align-items: center;
  gap: 14rpx;
}

.selected-item-title,
.selected-item-name,
.selected-item-label {
  display: block;
}

.selected-item-title {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.selected-item-name {
  font-size: 26rpx;
  font-weight: 900;
}

.selected-item-label {
  margin-top: 6rpx;
  font-size: 21rpx;
  font-weight: 800;
  opacity: 0.78;
}

.quantity-control {
  display: grid;
  grid-template-columns: 48rpx minmax(0, 1fr) 48rpx;
  gap: 6rpx;
  align-items: center;
}

.quantity-button,
.remove-item {
  margin: 0;
  padding: 0;
  border: 0;
}

.quantity-button {
  width: 48rpx;
  height: 48rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.8);
  color: inherit;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 48rpx;
}

.quantity-input {
  height: 48rpx;
  border-radius: 14rpx;
  background: rgba(255, 255, 255, 0.8);
  text-align: center;
  font-size: 24rpx;
  font-weight: 900;
}

.remove-item {
  width: 76rpx;
  height: 48rpx;
  border-radius: 16rpx;
  background: rgba(17, 24, 39, 0.1);
  color: inherit;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 48rpx;
}

.empty-line {
  margin-top: 20rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
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
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(17, 24, 39, 0.72);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 42rpx;
}

.photo-upload {
  margin: 0;
  padding: 0;
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
  margin: 0;
  padding: 0;
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
  border: 0;
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
