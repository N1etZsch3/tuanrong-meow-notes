<template>
  <view class="medicines-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="medicine-inner">
      <view class="medicine-fixed">
        <view class="page-title">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view class="title-copy">
            <view class="title-row">
              <text class="title-text">药品管理</text>
              <image class="title-icon" :src="medicineBookIcon" mode="aspectFit" />
            </view>
            <text class="title-subtitle">药品库存与用药协作</text>
          </view>
        </view>

        <view class="search-box">
          <text class="search-icon">⌕</text>
          <input
            v-model="searchKeyword"
            class="search-input"
            confirm-type="search"
            placeholder="搜索药品 / 规格 / 持有人"
            placeholder-class="search-placeholder"
            @confirm="handleSearchConfirm"
          />
          <button class="search-button" @tap="handleSearchConfirm">搜索</button>
        </view>

        <view class="filter-card">
          <picker
            class="filter-picker"
            :range="categoryOptions"
            range-key="label"
            :value="selectedCategoryIndex"
            @change="handleCategoryChange"
          >
            <view class="filter-control">
              <text class="picker-caption">药品分类</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedCategoryLabel }}</text>
                <image class="picker-arrow-icon" :src="filterArrowIcon" mode="aspectFit" />
              </view>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="MEDICINE_HOLDING_RELATION_OPTIONS"
            range-key="label"
            :value="selectedHoldingRelationIndex"
            @change="handleHoldingRelationChange"
          >
            <view class="filter-control">
              <text class="picker-caption">持有关系</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedHoldingRelationLabel }}</text>
                <image class="picker-arrow-icon" :src="filterArrowIcon" mode="aspectFit" />
              </view>
            </view>
          </picker>
          <button class="clear-filter-button" @tap="clearFilters">
            <image class="clear-filter-icon" :src="clearFilterIcon" mode="aspectFit" />
            <text>清除筛选</text>
          </button>
        </view>
      </view>

      <scroll-view class="medicine-scroll" scroll-y :show-scrollbar="false">
        <view class="medicine-list-body">
          <view v-if="loadState === 'loading'" class="state-box">
            <text class="state-title">正在加载药品库存</text>
            <text class="state-copy">马上整理好协会药品清单。</text>
          </view>

          <view v-else-if="loadState === 'error'" class="state-box">
            <text class="state-title">药品加载失败</text>
            <text class="state-copy">{{ errorMessage }}</text>
            <button class="retry-button" hover-class="button-hover" @tap="loadMedicines">
              重新加载
            </button>
          </view>

          <view v-else-if="medicines.length" class="medicine-list">
            <view
              v-for="medicine in medicines"
              :key="medicine.medicine_id"
              class="medicine-card"
              hover-class="button-hover"
              @tap="goMedicineDetail(medicine.medicine_id)"
            >
              <view class="medicine-image-wrap">
                <image
                  v-if="medicine.cover_image_url"
                  class="medicine-image"
                  :src="medicine.cover_image_url"
                  mode="aspectFill"
                />
                <view v-else class="medicine-image-placeholder">
                  <image class="placeholder-icon" :src="medicineIcon" mode="aspectFit" />
                </view>
              </view>
              <view class="medicine-main">
                <view class="medicine-head">
                  <text class="medicine-title">{{ medicine.name }}</text>
                  <text class="stock-pill" :class="getMedicineStockClass(medicine.stock_status)">
                    {{ medicine.stock_status_label }}
                  </text>
                </view>
                <text class="medicine-meta">
                  {{ medicine.category?.name || "未分类" }} · {{ medicine.specification || "暂无规格" }}
                </text>
                <view class="medicine-stats">
                  <text>{{ formatMedicineQuantity(medicine.total_current_quantity, medicine.unit) }}</text>
                  <text>{{ medicine.holder_count }} 位持有人</text>
                </view>
                <scroll-view class="holder-strip" scroll-x :show-scrollbar="false" @tap.stop>
                  <view class="holder-row">
                    <button
                      v-for="holder in medicine.holders"
                      :key="holder.holding_id"
                      class="holder-chip"
                      :class="{ mine: holder.is_current_user_holder }"
                      hover-class="button-hover"
                      @tap.stop="goHoldingDetail(holder.holding_id)"
                    >
                      {{ holder.holder_nickname }} ·
                      {{ formatMedicineQuantity(holder.current_quantity, holder.unit) }}
                    </button>
                  </view>
                </scroll-view>
              </view>
            </view>
          </view>

          <view v-else class="state-box">
            <text class="state-title">暂无药品记录</text>
            <text class="state-copy">从右下角新增药品，建立第一份库存。</text>
          </view>
        </view>
      </scroll-view>
    </view>
    <button class="floating-add" hover-class="button-hover" @tap="goCreateMedicine">
      新增药品
    </button>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import {
  getMedicineCategories,
  getMedicines,
  type MedicineCategoryDto,
  type MedicineListItemDto,
  type MedicineListQuery,
} from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  MEDICINE_HOLDING_RELATION_OPTIONS,
  formatMedicineQuantity,
  getMedicineStockClass,
} from "@/pages/medicines/medicine-page";

import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import medicineBookIcon from "../../../素材/svg/喵记/药品.svg";
import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import clearFilterIcon from "../../../素材/svg/猫咪库/删除.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";
type PickerChangeEvent = { detail: { value: string | number } };

const userStore = useUserStore();
const medicines = ref<MedicineListItemDto[]>([]);
const categories = ref<MedicineCategoryDto[]>([]);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const searchKeyword = ref("");
const selectedCategory = ref("");
const selectedHoldingRelation = ref<MedicineListQuery["holding_relation"]>("all");

const categoryOptions = computed(() => [
  { label: "全部", value: "" },
  ...categories.value.map((category) => ({
    label: category.name,
    value: category.id,
  })),
]);
const selectedCategoryIndex = computed(() =>
  Math.max(
    categoryOptions.value.findIndex((option) => option.value === selectedCategory.value),
    0,
  ),
);
const selectedHoldingRelationIndex = computed(() =>
  Math.max(
    MEDICINE_HOLDING_RELATION_OPTIONS.findIndex(
      (option) => option.value === selectedHoldingRelation.value,
    ),
    0,
  ),
);
const selectedCategoryLabel = computed(
  () => categoryOptions.value[selectedCategoryIndex.value]?.label || "全部",
);
const selectedHoldingRelationLabel = computed(
  () =>
    MEDICINE_HOLDING_RELATION_OPTIONS[selectedHoldingRelationIndex.value]?.label ||
    MEDICINE_HOLDING_RELATION_OPTIONS[0].label,
);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function loadCategories(token: string) {
  const data = await getMedicineCategories(token);
  categories.value = data.items;
}

function buildMedicineListQuery(): MedicineListQuery {
  return {
    keyword: searchKeyword.value.trim(),
    category_id: selectedCategory.value || undefined,
    holding_relation: selectedHoldingRelation.value,
    page: 1,
    page_size: 50,
  };
}

async function loadMedicines() {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  loadState.value = "loading";
  errorMessage.value = "";
  try {
    if (!categories.value.length) {
      await loadCategories(token);
    }
    const data = await getMedicines(token, buildMedicineListQuery());
    medicines.value = data.items;
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function pickerIndex(event: PickerChangeEvent): number {
  return Number(event.detail.value) || 0;
}

function handleSearchConfirm() {
  void loadMedicines();
}

function handleCategoryChange(event: PickerChangeEvent) {
  selectedCategory.value = categoryOptions.value[pickerIndex(event)]?.value || "";
  void loadMedicines();
}

function handleHoldingRelationChange(event: PickerChangeEvent) {
  selectedHoldingRelation.value =
    (MEDICINE_HOLDING_RELATION_OPTIONS[pickerIndex(event)]?.value ||
      "all") as MedicineListQuery["holding_relation"];
  void loadMedicines();
}

function clearFilters() {
  searchKeyword.value = "";
  selectedCategory.value = "";
  selectedHoldingRelation.value = "all";
  void loadMedicines();
}

function goBack() {
  uni.navigateBack();
}

function goCreateMedicine() {
  uni.navigateTo({ url: "/pages/medicines/create" });
}

function goMedicineDetail(medicineId: string) {
  uni.navigateTo({ url: `/pages/medicines/detail?medicine_id=${medicineId}` });
}

function goHoldingDetail(holdingId: string) {
  uni.navigateTo({ url: `/pages/medicines/holding?holding_id=${holdingId}` });
}

onShow(() => {
  void loadMedicines();
});
</script>

<style scoped>
.medicines-page {
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

.medicine-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 44rpx);
  display: flex;
  flex-direction: column;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.title-copy {
  min-width: 0;
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

.back-button,
.floating-add,
.search-button,
.clear-filter-button,
.holder-chip,
.retry-button {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.floating-add::after,
.search-button::after,
.clear-filter-button::after,
.holder-chip::after,
.retry-button::after {
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

.search-box,
.filter-card,
.medicine-card,
.state-box {
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
}

.search-box {
  min-height: 72rpx;
  margin-top: 30rpx;
  border-radius: 24rpx;
  padding: 0 14rpx 0 24rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.search-icon {
  color: #323946;
  font-size: 36rpx;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 72rpx;
  color: #222831;
  font-size: 25rpx;
}

.search-placeholder {
  color: #969da8;
}

.search-button {
  width: 84rpx;
  height: 50rpx;
  border-radius: 16rpx;
  background: #2f8a38;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 50rpx;
}

.filter-card {
  margin-top: 26rpx;
  border-radius: 26rpx;
  padding: 20rpx 18rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 82rpx;
  align-items: end;
  gap: 12rpx;
}

.picker-caption {
  display: block;
  margin: 0 0 10rpx 14rpx;
  color: rgba(82, 90, 102, 0.68);
  font-size: 19rpx;
  font-weight: 800;
}

.picker-shell {
  height: 58rpx;
  box-sizing: border-box;
  border: 2rpx solid #c4dac2;
  border-radius: 19rpx;
  padding: 0 12rpx 0 16rpx;
  background: rgba(255, 255, 255, 0.82);
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.picker-value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #151a20;
  font-size: 20rpx;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow-icon {
  width: 21rpx;
  height: 21rpx;
  transform: rotate(180deg);
}

.clear-filter-button {
  height: 82rpx;
  color: #0d9b2e;
  font-size: 18rpx;
  font-weight: 900;
  line-height: 1.1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 8rpx;
  background: transparent;
}

.clear-filter-icon {
  width: 32rpx;
  height: 32rpx;
}

.medicine-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 28rpx;
}

.medicine-list-body {
  padding-bottom: 130rpx;
}

.medicine-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.medicine-card {
  width: 100%;
  min-height: 210rpx;
  padding: 20rpx;
  border-radius: 28rpx;
  display: grid;
  grid-template-columns: 152rpx minmax(0, 1fr);
  gap: 20rpx;
}

.medicine-image-wrap,
.medicine-image,
.medicine-image-placeholder {
  width: 152rpx;
  height: 152rpx;
  border-radius: 22rpx;
  overflow: hidden;
}

.medicine-image-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 86rpx;
  height: 86rpx;
}

.medicine-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.medicine-head,
.medicine-stats {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14rpx;
}

.medicine-title {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.25;
}

.stock-pill {
  flex-shrink: 0;
  padding: 7rpx 12rpx;
  border-radius: 12rpx;
  font-size: 20rpx;
  font-weight: 900;
}

.stock-normal {
  background: #e6f6e4;
  color: #238033;
}

.stock-low {
  background: #fff4cc;
  color: #a66f00;
}

.stock-empty {
  background: #ffe7eb;
  color: #d73546;
}

.medicine-meta,
.medicine-stats {
  color: #4b5563;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.35;
}

.holder-strip {
  width: 100%;
  overflow: hidden;
  white-space: nowrap;
}

.holder-row {
  display: flex;
  gap: 10rpx;
}

.holder-chip {
  min-width: 132rpx;
  height: 54rpx;
  border-radius: 16rpx;
  background: #edf4ff;
  color: #2276ff;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 54rpx;
}

.holder-chip.mine {
  background: #e4f6dd;
  color: #237a2f;
}

.state-box {
  padding: 46rpx 34rpx;
  border-radius: 28rpx;
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
}

.retry-button {
  width: 168rpx;
  height: 64rpx;
  margin-top: 22rpx;
  border-radius: 20rpx;
  background: #e8f5e6;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 64rpx;
}

.floating-add {
  position: fixed;
  z-index: 5;
  right: 34rpx;
  bottom: calc(env(safe-area-inset-bottom) + 34rpx);
  width: 168rpx;
  height: 78rpx;
  border-radius: 999rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
