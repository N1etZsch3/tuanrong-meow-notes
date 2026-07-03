<template>
  <view class="detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">物资点详情</text>
            <text class="nav-subtitle">查看当前物资与历史记录</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载物资点详情</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">物资点详情加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
          <button class="retry-button" hover-class="button-hover" @tap="loadSupplyDetail">
            重新加载
          </button>
        </view>

        <view v-else-if="supply" class="detail-content">
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
                  @tap="openImagePreview(heroPhotoUrls, photo.url)"
                />
              </swiper-item>
            </swiper>
            <view v-else class="hero-placeholder">
              <image class="hero-placeholder-icon" :src="supplyIcon" mode="aspectFit" />
            </view>
          </view>

          <view class="title-block">
            <text class="eyebrow">物资点名称</text>
            <view class="title-row">
              <text class="page-title-text">{{ supply.name }}</text>
              <button
                v-if="canAdminEdit"
                class="edit-button"
                hover-class="button-hover"
                @tap="goEditSupplyPoint"
              >
                编辑
              </button>
            </view>
            <text class="desc-text">{{ supply.description || "暂无补充说明" }}</text>
          </view>

          <view class="info-panel">
            <view class="info-section material-section">
              <view class="info-section-head">
                <text class="info-label">物资详情</text>
                <text class="info-meta">{{ currentStateText }}</text>
              </view>
              <view v-if="supply.current_items.length" class="item-tags">
                <view
                  v-for="item in supply.current_items"
                  :key="item.source_item_id || item.item_id || item.label"
                  class="item-tag"
                  :class="`item-${item.color_key || 'gray'}`"
                >
                  <image
                    v-if="getSupplyItemIcon(item.icon_key)"
                    class="item-icon"
                    :src="getSupplyItemIcon(item.icon_key)"
                    mode="aspectFit"
                  />
                  <text>{{ item.label }}</text>
                </view>
              </view>
              <text v-else class="empty-line">暂无物资记录</text>
            </view>
            <view class="info-divider" />
            <view class="info-section address-section">
              <view class="info-section-head">
                <text class="info-label">地址</text>
                <view class="address-pin" />
              </view>
              <text class="address-title">{{ supply.map_point.location_name }}</text>
              <text class="address-detail">
                {{ supply.map_point.location_detail || "暂无详细地址" }}
              </text>
            </view>
          </view>

          <view v-if="associatedPoi" class="section-card poi-section">
            <view class="section-head">
              <text class="section-title">公共地点</text>
              <button class="small-button" hover-class="button-hover" @tap="goViewAssociatedPoiOnMap">
                地图查看
              </button>
            </view>
            <view class="section-line">
              <text class="section-line-label">名称</text>
              <text class="section-line-value">{{ associatedPoi.name }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">类别</text>
              <text class="section-line-value">{{ associatedPoi.category || "腾讯地图点位" }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">地址</text>
              <text class="section-line-value">{{ associatedPoi.address || "暂无地址" }}</text>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">路线说明</text>
            </view>
            <text class="route-text">
              {{ supply.map_point.route_instruction || supply.access_instruction || "暂无路线说明" }}
            </text>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">物资动态</text>
              <text class="section-meta">{{ supply.records.total }}</text>
            </view>
            <view class="filter-row">
              <button
                v-for="option in recordFilterOptions"
                :key="option.value"
                class="filter-button"
                :class="{ active: recordFilter === option.value }"
                hover-class="button-hover"
                @tap="changeRecordFilter(option.value)"
              >
                {{ option.label }}
              </button>
            </view>
            <scroll-view class="records-scroll" scroll-y :show-scrollbar="false">
              <view v-if="supply.records.items.length" class="record-list">
                <view
                  v-for="record in supply.records.items"
                  :key="record.record_id"
                  class="record-card"
                  :class="record.display_tone === 'danger' ? 'record-danger' : 'record-success'"
                >
                  <view class="record-head">
                    <view>
                      <text class="record-title">
                        {{ record.display_tone === "danger" ? "物资不一致" : "物资正常" }}
                      </text>
                      <text class="record-subtitle">
                        {{ record.recorder?.nickname || "成员" }} · {{ formatRecordTime(record.recorded_at) }}
                      </text>
                    </view>
                    <button class="record-view-button" hover-class="button-hover" @tap="openRecordModal(record)">
                      查看当日物资
                    </button>
                  </view>
                  <view class="item-tags compact-tags">
                    <view
                      v-for="item in record.items"
                      :key="`${record.record_id}-${item.source_item_id || item.label}`"
                      class="item-tag small-tag"
                      :class="`item-${item.color_key || 'gray'}`"
                    >
                      <image
                        v-if="getSupplyItemIcon(item.icon_key)"
                        class="item-icon small-icon"
                        :src="getSupplyItemIcon(item.icon_key)"
                        mode="aspectFit"
                      />
                      <text>{{ item.label }}</text>
                    </view>
                  </view>
                </view>
              </view>
              <text v-else class="empty-line">暂无物资动态</text>
            </scroll-view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="supply" class="bottom-actions">
      <button class="ghost-action" hover-class="button-hover" @tap="goNavigateToSupplyPoint">
        导航前往
      </button>
      <button class="primary-action" hover-class="button-hover" @tap="openRecordForm">
        记录物资
      </button>
    </view>

    <view v-if="recordFormVisible" class="modal-mask" @tap="closeRecordForm">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">记录物资</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeRecordForm">×</button>
        </view>
        <text class="modal-hint">勾选当前物资点实际拥有的物资，并上传一张现场照片。</text>
        <view class="record-tag-grid">
          <button
            v-for="item in recordSelectableItems"
            :key="item.item_id || item.label"
            class="record-select-tag"
            :class="[
              `item-${item.color_key || 'gray'}`,
              { selected: isRecordItemSelected(item.item_id) },
            ]"
            hover-class="button-hover"
            @tap="toggleRecordItem(item.item_id)"
          >
            <image
              v-if="getSupplyItemIcon(item.icon_key)"
              class="item-icon"
              :src="getSupplyItemIcon(item.icon_key)"
              mode="aspectFit"
            />
            {{ item.label }}
          </button>
        </view>
        <view class="record-photo-box">
          <image
            v-if="recordPhoto"
            class="record-photo"
            :src="recordPhoto.thumbnail_url || recordPhoto.file_url"
            mode="aspectFill"
          />
          <button
            v-else
            class="record-photo-upload"
            :loading="isUploadingRecordPhoto"
            hover-class="button-hover"
            @tap="chooseRecordPhoto"
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
          :loading="isSubmittingRecord"
          hover-class="button-hover"
          @tap="submitSupplyRecord"
        >
          完成记录
        </button>
      </view>
    </view>

    <view v-if="viewingRecord" class="modal-mask" @tap="closeRecordModal">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">物资情况</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeRecordModal">×</button>
        </view>
        <text class="modal-hint">{{ formatRecordTime(viewingRecord.recorded_at) }}</text>
        <view class="item-tags modal-tags">
          <view
            v-for="item in viewingRecord.items"
            :key="`${viewingRecord.record_id}-${item.source_item_id || item.label}`"
            class="item-tag"
            :class="`item-${item.color_key || 'gray'}`"
          >
            <image
              v-if="getSupplyItemIcon(item.icon_key)"
              class="item-icon"
              :src="getSupplyItemIcon(item.icon_key)"
              mode="aspectFit"
            />
            <text>{{ item.label }}</text>
          </view>
        </view>
        <image
          class="modal-record-image"
          :src="viewingRecord.photo.thumbnail_url || viewingRecord.photo.file_url"
          mode="aspectFill"
        />
      </view>
    </view>

    <ImagePreviewModal
      :visible="imagePreviewVisible"
      :images="imagePreviewUrls"
      :current-index="imagePreviewIndex"
      @change="setImagePreviewIndex"
      @close="closeImagePreview"
    />
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { uploadImage } from "@/api/files";
import {
  createSupplyRecord,
  getSupplyPointDetail,
  type SupplyItemDto,
  type SupplyPointDetailDto,
  type SupplyRecordDto,
  type UploadedFileRef,
} from "@/api/supplies";
import ImagePreviewModal from "@/components/ImagePreviewModal.vue";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  buildSupplyRecordFilterQuery,
  buildUploadedSupplyPhoto,
  formatRecordTime,
  getSupplyPhotoDisplayUrl,
  type SupplyRecordFilterValue,
} from "@/pages/admin/supplies/supply-page";
import { MAP_PENDING_NAVIGATION_STORAGE_KEY } from "@/pages/index/map-page";

import supplyIcon from "../../../素材/icon/物资.png";
import carrierIcon from "../../../素材/svg/物资点/航空箱.svg";
import catFoodIcon from "../../../素材/svg/物资点/猫粮.svg";
import glovesIcon from "../../../素材/svg/物资点/手套.svg";
import netIcon from "../../../素材/svg/物资点/网兜.svg";
import trapIcon from "../../../素材/svg/物资点/诱捕笼.svg";
import waterIcon from "../../../素材/svg/物资点/水.svg";
import loadingBackground from "../../../素材/加载页素材/加载页背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const supplyPointId = ref("");
const supply = ref<SupplyPointDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const recordFilter = ref<SupplyRecordFilterValue>("all");
const recordFormVisible = ref(false);
const selectedRecordItemIds = ref<string[]>([]);
const recordPhoto = ref<UploadedFileRef | null>(null);
const recordRemark = ref("");
const isUploadingRecordPhoto = ref(false);
const isSubmittingRecord = ref(false);
const viewingRecord = ref<SupplyRecordDto | null>(null);
const imagePreviewVisible = ref(false);
const imagePreviewUrls = ref<string[]>([]);
const imagePreviewIndex = ref(0);
const recordFilterOptions: Array<{ value: SupplyRecordFilterValue; label: string }> = [
  { value: "all", label: "全部" },
  { value: "month", label: "本月" },
  { value: "week", label: "本周" },
  { value: "day", label: "今天" },
];
const supplyItemIcons: Record<string, string> = {
  carrier: carrierIcon,
  cat_food: catFoodIcon,
  gloves: glovesIcon,
  net: netIcon,
  trap: trapIcon,
  water: waterIcon,
};

const heroPhotos = computed(() =>
  (supply.value?.photos || [])
    .map((photo) => ({ photo_id: photo.photo_id, url: getSupplyPhotoDisplayUrl(photo) }))
    .filter((photo) => photo.url),
);
const heroPhotoUrls = computed(() => heroPhotos.value.map((photo) => photo.url));
const associatedPoi = computed(() => supply.value?.map_point.associated_poi || null);
const canAdminEdit = computed(() => userStore.isAdmin);
const currentStateText = computed(() =>
  supply.value?.current_state_source === "latest_record" ? "来自最新记录" : "来自初始配置",
);
const recordSelectableItems = computed(() =>
  (supply.value?.initial_items || []).filter((item) => item.item_id),
);

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

async function loadSupplyDetail() {
  const token = await getAccessToken();
  if (!token || !supplyPointId.value) {
    loadState.value = "error";
    errorMessage.value = "缺少物资点 ID";
    return;
  }
  loadState.value = "loading";
  try {
    supply.value = await getSupplyPointDetail(token, supplyPointId.value, {
      ...buildSupplyRecordFilterQuery(recordFilter.value),
      record_page_size: 50,
    });
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function changeRecordFilter(value: SupplyRecordFilterValue) {
  recordFilter.value = value;
  void loadSupplyDetail();
}

function openRecordForm() {
  selectedRecordItemIds.value = (supply.value?.current_items || [])
    .map((item) => item.source_item_id || item.item_id || "")
    .filter((id) => id);
  recordPhoto.value = null;
  recordRemark.value = "";
  recordFormVisible.value = true;
}

function closeRecordForm() {
  if (isSubmittingRecord.value) {
    return;
  }
  recordFormVisible.value = false;
}

function isRecordItemSelected(itemId: string | null): boolean {
  return Boolean(itemId && selectedRecordItemIds.value.includes(itemId));
}

function toggleRecordItem(itemId: string | null) {
  if (!itemId) {
    return;
  }
  if (selectedRecordItemIds.value.includes(itemId)) {
    selectedRecordItemIds.value = selectedRecordItemIds.value.filter((id) => id !== itemId);
    return;
  }
  selectedRecordItemIds.value = [...selectedRecordItemIds.value, itemId];
}

function chooseRecordPhoto() {
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const path = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths[0]
        : result.tempFilePaths;
      if (path) {
        void uploadRecordPhoto(path);
      }
    },
  });
}

async function uploadRecordPhoto(path: string) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isUploadingRecordPhoto.value = true;
  try {
    const asset = await uploadImage(token, path, {
      usage_type: "supply_record_photo",
      owner_type: "supply_point_record",
      visibility: "internal",
      caption: "物资记录照片",
    });
    recordPhoto.value = buildUploadedSupplyPhoto(asset);
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploadingRecordPhoto.value = false;
  }
}

function recordPayloadItems() {
  const initialById = new Map(
    recordSelectableItems.value.map((item: SupplyItemDto) => [item.item_id, item]),
  );
  return selectedRecordItemIds.value
    .map((itemId) => {
      const item = initialById.get(itemId);
      return item
        ? {
            item_id: itemId,
            quantity: item.quantity,
          }
        : null;
    })
    .filter((item): item is { item_id: string; quantity: number } => Boolean(item));
}

async function submitSupplyRecord() {
  if (!selectedRecordItemIds.value.length) {
    uni.showToast({ title: "请勾选物资标签", icon: "none" });
    return;
  }
  if (!recordPhoto.value) {
    uni.showToast({ title: "请上传物资点照片", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token || !supply.value || isSubmittingRecord.value) {
    return;
  }
  isSubmittingRecord.value = true;
  try {
    await createSupplyRecord(token, supply.value.supply_point_id, {
      items: recordPayloadItems(),
      photo: recordPhoto.value,
      remark: recordRemark.value || null,
    });
    uni.showToast({ title: "物资已记录", icon: "success" });
    recordFormVisible.value = false;
    await loadSupplyDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "提交失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmittingRecord.value = false;
  }
}

function openRecordModal(record: SupplyRecordDto) {
  viewingRecord.value = record;
}

function closeRecordModal() {
  viewingRecord.value = null;
}

function openImagePreview(urls: string[], current: string) {
  if (!current) {
    return;
  }
  const uniqueUrls = Array.from(new Set(urls.filter((url) => url)));
  const resolvedUrls = uniqueUrls.length ? uniqueUrls : [current];
  imagePreviewUrls.value = resolvedUrls;
  imagePreviewIndex.value = Math.max(0, resolvedUrls.indexOf(current));
  imagePreviewVisible.value = true;
}

function closeImagePreview() {
  imagePreviewVisible.value = false;
}

function setImagePreviewIndex(index: number) {
  imagePreviewIndex.value = index;
}

function goNavigateToSupplyPoint() {
  if (!supply.value) {
    return;
  }
  uni.setStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY, {
    source: "supply_detail",
    map_point_id: supply.value.map_point_id,
    shell_item: {
      id: supply.value.supply_point_id,
      map_point_id: supply.value.map_point_id,
      type: "supply",
      title: supply.value.name,
      subtitle: supply.value.map_point.location_name,
      description: supply.value.map_point.location_detail,
      distance_meters: null,
      status_label: "查看",
      status_key: supply.value.status,
      tag_label: "物资点",
      lng: supply.value.map_point.lng,
      lat: supply.value.map_point.lat,
      cover_photo_url: supply.value.photos[0]?.thumbnail_url || supply.value.photos[0]?.file_url || null,
      icon_key: "supply_food",
      associated_poi: supply.value.map_point.associated_poi || null,
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
    source: "supply_detail_poi",
    poi,
  });
  uni.switchTab({ url: "/pages/index/index" });
}

function goEditSupplyPoint() {
  if (!supply.value) {
    return;
  }
  uni.navigateTo({
    url: `/pages/admin/supplies/create?mode=edit&supply_point_id=${supply.value.supply_point_id}`,
  });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  supplyPointId.value =
    typeof query?.supply_point_id === "string" ? query.supply_point_id : "";
  void loadSupplyDetail();
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
.small-button::after,
.edit-button::after,
.ghost-action::after,
.primary-action::after,
.filter-button::after,
.record-view-button::after,
.modal-close::after,
.record-select-tag::after,
.record-photo-upload::after,
.modal-submit::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.state-title,
.state-copy,
.eyebrow,
.page-title-text,
.desc-text,
.info-label,
.info-meta,
.section-title,
.section-line,
.section-line-label,
.section-line-value,
.section-meta,
.empty-line,
.record-title,
.record-subtitle,
.route-text,
.modal-title,
.modal-hint {
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

.title-row {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 104rpx;
  align-items: center;
  gap: 18rpx;
}

.page-title-text {
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.edit-button,
.retry-button,
.small-button {
  margin: 0;
  padding: 0;
  border: 0;
  background: #e8f5e6;
  color: #287c31;
  font-weight: 900;
}

.edit-button {
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

.desc-text {
  margin-top: 18rpx;
  color: #465160;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
}

.info-panel,
.section-card,
.state-box {
  box-sizing: border-box;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.info-panel {
  margin-top: 34rpx;
  overflow: hidden;
  border: 2rpx solid rgba(212, 237, 208, 0.72);
}

.info-section {
  padding: 28rpx;
}

.material-section {
  background: rgba(247, 252, 246, 0.78);
}

.address-section {
  background: rgba(255, 255, 255, 0.68);
}

.info-divider {
  height: 1rpx;
  margin: 0 28rpx;
  background: rgba(189, 214, 185, 0.72);
}

.info-section-head,
.section-head,
.record-head,
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.info-label,
.section-meta,
.empty-line,
.record-subtitle,
.info-meta {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.item-tags {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.compact-tags {
  margin-top: 16rpx;
}

.item-tag {
  padding: 10rpx 16rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 23rpx;
  font-weight: 900;
}

.item-icon {
  width: 30rpx;
  height: 30rpx;
}

.small-icon {
  width: 26rpx;
  height: 26rpx;
}

.small-tag {
  font-size: 21rpx;
}

.item-green {
  background: #e4f6dd;
  color: #237a2f;
}

.item-blue {
  background: #dff1ff;
  color: #1d6fb8;
}

.item-purple {
  background: #efe8ff;
  color: #6d42b8;
}

.item-teal {
  background: #def7f0;
  color: #167766;
}

.item-orange {
  background: #fff0d9;
  color: #a45b00;
}

.item-red {
  background: #ffe6e6;
  color: #c43b3b;
}

.item-gray {
  background: #edf0f3;
  color: #526070;
}

.address-title,
.address-detail {
  display: block;
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

.section-card,
.state-box {
  margin-top: 24rpx;
  padding: 30rpx;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.small-button {
  width: 126rpx;
  height: 56rpx;
  border-radius: 18rpx;
  font-size: 23rpx;
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

.section-line-value,
.route-text {
  color: #273040;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.55;
}

.section-line-value {
  flex: 1;
  min-width: 0;
}

.route-text {
  margin-top: 18rpx;
}

.filter-row {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.filter-button {
  height: 56rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #eef4ec;
  color: #526070;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 56rpx;
}

.filter-button.active {
  background: #287c31;
  color: #ffffff;
}

.records-scroll {
  max-height: 560rpx;
  margin-top: 20rpx;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.record-card {
  box-sizing: border-box;
  padding: 22rpx;
  border-radius: 22rpx;
}

.record-success {
  background: #edf8e8;
  border: 2rpx solid rgba(91, 177, 86, 0.28);
}

.record-danger {
  background: #ffe8e8;
  border: 2rpx solid rgba(215, 53, 70, 0.24);
}

.record-title {
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.record-subtitle {
  margin-top: 8rpx;
}

.record-view-button {
  width: 170rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #287c31;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
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

.modal-mask {
  position: fixed;
  z-index: 20;
  inset: 0;
  background: rgba(17, 24, 39, 0.42);
  display: flex;
  align-items: flex-end;
}

.modal-panel {
  box-sizing: border-box;
  width: 100%;
  max-height: 82vh;
  padding: 30rpx 30rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -18rpx 46rpx rgba(17, 24, 39, 0.18);
}

.modal-title {
  color: #111827;
  font-size: 34rpx;
  font-weight: 900;
}

.modal-close {
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #edf0f3;
  color: #526070;
  font-size: 36rpx;
  line-height: 54rpx;
}

.modal-hint {
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.45;
}

.record-tag-grid,
.modal-tags {
  margin-top: 22rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.record-select-tag {
  min-height: 62rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 3rpx solid transparent;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.record-select-tag.selected {
  border-color: #287c31;
  box-shadow: 0 8rpx 18rpx rgba(40, 124, 49, 0.16);
}

.record-photo-box {
  margin-top: 24rpx;
}

.record-photo,
.record-photo-upload {
  width: 180rpx;
  height: 180rpx;
  border-radius: 24rpx;
}

.record-photo-upload {
  margin: 0;
  padding: 0;
  border: 2rpx dashed rgba(40, 124, 49, 0.5);
  background: #f4fbef;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 176rpx;
}

.record-remark {
  box-sizing: border-box;
  width: 100%;
  min-height: 132rpx;
  margin-top: 24rpx;
  padding: 22rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.24);
  border-radius: 22rpx;
  color: #111827;
  font-size: 25rpx;
  font-weight: 700;
}

.placeholder {
  color: #8b919b;
}

.modal-submit {
  width: 100%;
  height: 84rpx;
  margin: 24rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 84rpx;
}

.modal-record-image {
  width: 100%;
  height: 420rpx;
  margin-top: 24rpx;
  border-radius: 24rpx;
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

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
