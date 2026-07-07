<template>
  <view class="medicine-form-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="form-scroll" scroll-y :show-scrollbar="false">
      <view class="form-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">新增药品</text>
            <text class="nav-subtitle">输入名称后可关联药品库主档</text>
          </view>
        </view>

        <view class="section-card">
          <text class="section-title">药品信息</text>
          <view class="field-group">
            <text class="field-label">药品名称</text>
            <view v-if="isCatalogLinked" class="selected-medicine-tag">
              <text class="tag-name">{{ draft.name }}</text>
              <button class="tag-remove" hover-class="button-hover" @tap="clearSelectedMedicine">
                ×
              </button>
            </view>
            <input
              v-else
              v-model.trim="draft.name"
              class="form-input"
              placeholder="如：阿莫西林"
              placeholder-class="placeholder"
              @input="handleMedicineNameInput"
              @focus="handleMedicineNameInput"
              @confirm="loadCatalogSuggestions"
            />
            <scroll-view
              v-if="showCatalogSuggestions"
              class="catalog-suggestion-list"
              scroll-y
              :show-scrollbar="false"
            >
              <button
                v-for="medicine in catalogSuggestions"
                :key="medicine.medicine_id"
                class="catalog-suggestion-card"
                hover-class="button-hover"
                @tap="selectExistingMedicine(medicine)"
              >
                <image
                  v-if="medicine.cover_image_url"
                  class="suggestion-cover"
                  :src="medicine.cover_image_url"
                  mode="aspectFill"
                />
                <view class="suggestion-copy">
                  <text class="suggestion-name">{{ medicine.name }}</text>
                  <text class="suggestion-meta">
                    {{ medicine.specification || "暂无规格" }} · {{ medicine.unit }}
                  </text>
                  <text v-if="medicine.category?.name || medicine.category_name" class="suggestion-category">
                    {{ medicine.category?.name || medicine.category_name }}
                  </text>
                </view>
              </button>
              <text v-if="isSearchingCatalog && !catalogSuggestions.length" class="hint-line">
                正在查询药品库...
              </text>
            </scroll-view>
            <text v-if="manualCatalogHintVisible" class="hint-line">
              不点选候选项时，将按当前填写内容保存为新的药品主档。
            </text>
          </view>

          <view class="field-group">
            <text class="field-label">药品分类</text>
            <picker
              :disabled="isCatalogLinked"
              :range="categoryOptions"
              range-key="label"
              :value="selectedCategoryIndex"
              @change="handleCategoryChange"
            >
              <view class="picker-shell" :class="{ disabled: isCatalogLinked }">
                <text>{{ selectedCategoryLabel }}</text>
                <image class="picker-arrow-icon" :src="filterArrowIcon" mode="aspectFit" />
              </view>
            </picker>
          </view>
          <view class="field-grid">
            <view class="field-group">
              <text class="field-label">规格</text>
              <input
                v-model.trim="draft.specification"
                class="form-input"
                :disabled="isCatalogLinked"
                placeholder="250mg/片"
                placeholder-class="placeholder"
              />
            </view>
            <view class="field-group">
              <text class="field-label">计量单位</text>
              <input
                v-model.trim="draft.unit"
                class="form-input"
                :disabled="isCatalogLinked"
                placeholder="片 / 支 / 瓶"
                placeholder-class="placeholder"
              />
            </view>
          </view>
          <view class="field-group">
            <text class="field-label">药品图片</text>
            <text class="field-hint">最多上传 5 张，第一张将作为封面。</text>
            <view class="medicine-photo-row">
              <view
                v-for="photo in draft.photo_urls"
                :key="photo"
                class="medicine-photo-card"
              >
                <image class="medicine-photo" :src="photo" mode="aspectFill" />
                <button
                  v-if="!isCatalogLinked"
                  class="photo-remove"
                  hover-class="button-hover"
                  @tap="removeMedicineImage(photo)"
                >
                  ×
                </button>
              </view>
              <button
                v-if="!isCatalogLinked && remainingImageSlots > 0"
                class="photo-upload"
                :loading="isUploadingImage"
                hover-class="button-hover"
                @tap="chooseMedicineImage"
              >
                +
              </button>
              <text v-if="!isCatalogLinked" class="hint-line">
                已上传 {{ draft.photo_urls.length }}/{{ MEDICINE_IMAGE_LIMIT }} 张
              </text>
              <text v-if="isCatalogLinked" class="hint-line">
                图片来自已关联的药品主档，取消关联后可重新上传。
              </text>
            </view>
          </view>
          <view class="field-group">
            <text class="field-label">药品说明</text>
            <textarea
              v-model.trim="draft.description"
              class="form-textarea"
              :disabled="isCatalogLinked"
              maxlength="500"
              placeholder="用途、适用场景，可不填"
              placeholder-class="placeholder"
            />
          </view>
          <view class="field-group">
            <text class="field-label">用药注意</text>
            <textarea
              v-model.trim="draft.usage_notes"
              class="form-textarea"
              :disabled="isCatalogLinked"
              maxlength="500"
              placeholder="剂量、禁忌、需线下确认事项"
              placeholder-class="placeholder"
            />
          </view>
        </view>

        <view class="section-card">
          <text class="section-title">持有库存</text>
          <view class="field-group">
            <text class="field-label">持有人</text>
            <view v-if="!canAssignHolder" class="readonly-holder">
              <text>{{ currentUserLabel }}</text>
              <text class="holder-hint">成员新增药品时默认由本人持有。</text>
            </view>
            <view v-else>
              <view v-if="selectedHolder" class="selected-medicine-tag">
                <text class="tag-name">{{ selectedHolderLabel }}</text>
                <button class="tag-remove" hover-class="button-hover" @tap="clearSelectedHolder">
                  ×
                </button>
              </view>
              <input
                v-else
                v-model.trim="holderKeyword"
                class="form-input"
                placeholder="搜索昵称 / 喵喵号 / 姓名"
                placeholder-class="placeholder"
                @input="handleHolderKeywordInput"
                @focus="handleHolderKeywordInput"
                @confirm="loadHolderSuggestions"
              />
              <scroll-view
                v-if="showHolderSuggestions"
                class="holder-suggestion-list"
                scroll-y
                :show-scrollbar="false"
              >
                <button
                  v-for="holder in holderSuggestions"
                  :key="holder.id"
                  class="holder-suggestion-card"
                  hover-class="button-hover"
                  @tap="selectHolder(holder)"
                >
                  <text class="suggestion-name">
                    {{ holder.profile.nickname || "未命名成员" }}
                  </text>
                  <text class="suggestion-meta">
                    {{ holder.meow_no || holder.student_no }} · {{ holder.role }}
                  </text>
                </button>
                <text v-if="isSearchingHolder && !holderSuggestions.length" class="hint-line">
                  正在查询成员...
                </text>
              </scroll-view>
              <text v-if="!selectedHolder" class="hint-line">
                留空时默认由本人持有；输入后请从列表中选择持有人。
              </text>
            </view>
          </view>
          <view class="field-grid">
            <view class="field-group">
              <text class="field-label">初始数量</text>
              <input
                v-model.number="draft.initial_quantity"
                class="form-input"
                type="digit"
                placeholder="0"
                placeholder-class="placeholder"
              />
            </view>
            <view class="field-group">
              <text class="field-label">备注</text>
              <input
                v-model.trim="draft.remark"
                class="form-input"
                placeholder="如来源、保管说明"
                placeholder-class="placeholder"
              />
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="bottom-actions">
      <button class="ghost-action" hover-class="button-hover" @tap="goBack">取消</button>
      <button
        class="primary-action"
        :loading="isSubmitting"
        hover-class="button-hover"
        @tap="submitMedicine"
      >
        保存药品
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { listAdminUsers, type AdminUserDto } from "@/api/admin-users";
import { uploadImage } from "@/api/files";
import {
  createMedicine,
  getMedicineCategories,
  searchMedicines,
  type MedicineCategoryDto,
  type MedicineSearchItemDto,
} from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import {
  applySelectedMedicineToDraft,
  buildMedicineCreatePayload,
  clearSelectedMedicineDraft,
  createDefaultMedicineDraft,
  isMedicineCatalogLinked,
  validateMedicineCreateDraft,
} from "@/pages/medicines/medicine-page";

import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type PickerChangeEvent = { detail: { value: string | number } };

const userStore = useUserStore();
const MEDICINE_IMAGE_LIMIT = 5;
const draft = ref(createDefaultMedicineDraft());
const categories = ref<MedicineCategoryDto[]>([]);
const catalogSuggestions = ref<MedicineSearchItemDto[]>([]);
const holderKeyword = ref("");
const holderSuggestions = ref<AdminUserDto[]>([]);
const selectedHolder = ref<AdminUserDto | null>(null);
const hasSearchedCatalog = ref(false);
const isSearchingCatalog = ref(false);
const isSearchingHolder = ref(false);
const isUploadingImage = ref(false);
const isSubmitting = ref(false);
let searchTimer: ReturnType<typeof setTimeout> | null = null;
let holderSearchTimer: ReturnType<typeof setTimeout> | null = null;
let searchRequestSeq = 0;
let holderSearchRequestSeq = 0;

const isCatalogLinked = computed(() => isMedicineCatalogLinked(draft.value));
const canAssignHolder = computed(() => userStore.isAdmin);
const remainingImageSlots = computed(() =>
  Math.max(MEDICINE_IMAGE_LIMIT - draft.value.photo_urls.length, 0),
);
const currentUserLabel = computed(() => {
  const user = userStore.currentUser;
  if (!user) {
    return "我自己";
  }
  return `${user.nickname || "我自己"}（${user.meow_no || user.student_no}）`;
});
const selectedHolderLabel = computed(() => {
  const holder = selectedHolder.value;
  if (!holder) {
    return "";
  }
  return `${holder.profile.nickname || "未命名成员"}（${holder.meow_no || holder.student_no}）`;
});
const categoryOptions = computed(() => [
  { label: "请选择分类", value: "" },
  ...categories.value.map((category) => ({
    label: category.name,
    value: category.id,
  })),
]);
const selectedCategoryIndex = computed(() =>
  Math.max(
    categoryOptions.value.findIndex((option) => option.value === draft.value.category_id),
    0,
  ),
);
const selectedCategoryLabel = computed(
  () => categoryOptions.value[selectedCategoryIndex.value]?.label || "请选择分类",
);
const showCatalogSuggestions = computed(
  () =>
    !isCatalogLinked.value &&
    draft.value.name.trim().length > 0 &&
    (catalogSuggestions.value.length > 0 || isSearchingCatalog.value),
);
const manualCatalogHintVisible = computed(
  () =>
    !isCatalogLinked.value &&
    hasSearchedCatalog.value &&
    draft.value.name.trim().length > 0 &&
    !isSearchingCatalog.value,
);
const showHolderSuggestions = computed(
  () =>
    canAssignHolder.value &&
    !selectedHolder.value &&
    holderKeyword.value.trim().length > 0 &&
    (holderSuggestions.value.length > 0 || isSearchingHolder.value),
);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function loadCategories() {
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  const data = await getMedicineCategories(token);
  categories.value = data.items;
}

function pickerIndex(event: PickerChangeEvent): number {
  return Number(event.detail.value) || 0;
}

function handleCategoryChange(event: PickerChangeEvent) {
  if (isCatalogLinked.value) {
    return;
  }
  draft.value.category_id = categoryOptions.value[pickerIndex(event)]?.value || "";
}

function readInputValue(event: unknown): string | null {
  const detail = (event as { detail?: unknown } | undefined)?.detail;
  if (detail && typeof detail === "object" && "value" in detail) {
    const value = (detail as { value?: unknown }).value;
    return typeof value === "string" ? value : null;
  }
  return typeof detail === "string" ? detail : null;
}

function handleMedicineNameInput(event?: unknown) {
  if (isCatalogLinked.value) {
    return;
  }
  const inputValue = readInputValue(event);
  if (inputValue !== null) {
    draft.value.name = inputValue;
  }
  scheduleCatalogSearch();
}

function scheduleCatalogSearch() {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  const keyword = draft.value.name.trim();
  if (!keyword) {
    catalogSuggestions.value = [];
    hasSearchedCatalog.value = false;
    isSearchingCatalog.value = false;
    return;
  }
  searchTimer = setTimeout(() => {
    void loadCatalogSuggestions();
  }, 260);
}

async function loadCatalogSuggestions() {
  const keyword = draft.value.name.trim();
  if (!keyword || isCatalogLinked.value) {
    catalogSuggestions.value = [];
    hasSearchedCatalog.value = false;
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  const requestId = ++searchRequestSeq;
  isSearchingCatalog.value = true;
  try {
    const data = await searchMedicines(token, keyword);
    if (requestId === searchRequestSeq) {
      catalogSuggestions.value = data.items;
      hasSearchedCatalog.value = true;
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "查询药品库失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    if (requestId === searchRequestSeq) {
      isSearchingCatalog.value = false;
    }
  }
}

function selectExistingMedicine(medicine: MedicineSearchItemDto) {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  draft.value = applySelectedMedicineToDraft(draft.value, medicine);
  catalogSuggestions.value = [];
  hasSearchedCatalog.value = false;
  isSearchingCatalog.value = false;
}

function clearSelectedMedicine() {
  draft.value = clearSelectedMedicineDraft(draft.value);
  catalogSuggestions.value = [];
  hasSearchedCatalog.value = false;
  isSearchingCatalog.value = false;
}

function handleHolderKeywordInput(event?: unknown) {
  if (!canAssignHolder.value || selectedHolder.value) {
    return;
  }
  const inputValue = readInputValue(event);
  if (inputValue !== null) {
    holderKeyword.value = inputValue;
  }
  scheduleHolderSearch();
}

function scheduleHolderSearch() {
  if (holderSearchTimer) {
    clearTimeout(holderSearchTimer);
  }
  const keyword = holderKeyword.value.trim();
  draft.value.holder_id = "";
  if (!keyword) {
    holderSuggestions.value = [];
    isSearchingHolder.value = false;
    return;
  }
  holderSearchTimer = setTimeout(() => {
    void loadHolderSuggestions();
  }, 260);
}

async function loadHolderSuggestions() {
  const keyword = holderKeyword.value.trim();
  if (!keyword || !canAssignHolder.value || selectedHolder.value) {
    holderSuggestions.value = [];
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  const requestId = ++holderSearchRequestSeq;
  isSearchingHolder.value = true;
  try {
    const data = await listAdminUsers(token, {
      page: 1,
      page_size: 8,
      keyword,
      status: "active",
      sort_by: "meow_no",
      sort_order: "asc",
    });
    if (requestId === holderSearchRequestSeq) {
      holderSuggestions.value = data.items;
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "查询成员失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    if (requestId === holderSearchRequestSeq) {
      isSearchingHolder.value = false;
    }
  }
}

function selectHolder(holder: AdminUserDto) {
  if (holderSearchTimer) {
    clearTimeout(holderSearchTimer);
  }
  selectedHolder.value = holder;
  draft.value.holder_id = holder.id;
  holderKeyword.value = selectedHolderLabel.value;
  holderSuggestions.value = [];
  isSearchingHolder.value = false;
}

function clearSelectedHolder() {
  selectedHolder.value = null;
  draft.value.holder_id = "";
  holderKeyword.value = "";
  holderSuggestions.value = [];
  isSearchingHolder.value = false;
}

function chooseMedicineImage() {
  if (isCatalogLinked.value) {
    return;
  }
  if (remainingImageSlots.value <= 0) {
    uni.showToast({ title: "最多上传 5 张图片", icon: "none" });
    return;
  }
  uni.chooseImage({
    count: remainingImageSlots.value,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths].filter(Boolean);
      if (paths.length) {
        void uploadMedicineImages(paths.slice(0, remainingImageSlots.value));
      }
    },
  });
}

async function uploadMedicineImages(paths: string[]) {
  const token = await getAccessToken();
  if (!token || !paths.length) {
    return;
  }
  isUploadingImage.value = true;
  try {
    const uploadedUrls: string[] = [];
    for (const path of paths) {
      if (draft.value.photo_urls.length + uploadedUrls.length >= MEDICINE_IMAGE_LIMIT) {
        break;
      }
      const asset = await uploadImage(token, path, {
        usage_type: "medicine_photo",
        owner_type: "medicine_catalog",
        visibility: "internal",
        caption: "药品图片",
      });
      uploadedUrls.push(asset.default_url);
    }
    const nextPhotos = [...draft.value.photo_urls, ...uploadedUrls].slice(
      0,
      MEDICINE_IMAGE_LIMIT,
    );
    draft.value.photo_urls = nextPhotos;
    draft.value.cover_image_url = nextPhotos[0] || "";
    uni.showToast({ title: "图片已上传", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploadingImage.value = false;
  }
}

function removeMedicineImage(photo: string) {
  if (!isCatalogLinked.value) {
    draft.value.photo_urls = draft.value.photo_urls.filter((item) => item !== photo);
    draft.value.cover_image_url = draft.value.photo_urls[0] || "";
  }
}

async function submitMedicine() {
  if (canAssignHolder.value && holderKeyword.value.trim() && !selectedHolder.value) {
    uni.showToast({ title: "请从列表中选择持有人", icon: "none" });
    return;
  }
  const validation = validateMedicineCreateDraft(draft.value);
  if (!validation.valid) {
    uni.showToast({ title: validation.message || "请完善药品信息", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token || isSubmitting.value) {
    return;
  }

  isSubmitting.value = true;
  try {
    const response = await createMedicine(token, buildMedicineCreatePayload(draft.value));
    uni.showToast({ title: "药品已保存", icon: "success" });
    uni.redirectTo({ url: `/pages/medicines/detail?medicine_id=${response.medicine_id}` });
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

onLoad(() => {
  void loadCategories();
});
</script>

<style scoped>
.medicine-form-page {
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

.form-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.form-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 160rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button,
.catalog-suggestion-card,
.holder-suggestion-card,
.tag-remove,
.photo-remove,
.photo-upload,
.ghost-action,
.primary-action {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.catalog-suggestion-card::after,
.holder-suggestion-card::after,
.tag-remove::after,
.photo-remove::after,
.photo-upload::after,
.ghost-action::after,
.primary-action::after {
  border: 0;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.nav-title,
.nav-subtitle,
.section-title,
.field-label,
.field-hint,
.hint-line,
.holder-hint,
.suggestion-name,
.suggestion-meta,
.suggestion-category,
.tag-name {
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
}

.section-card {
  box-sizing: border-box;
  margin-top: 26rpx;
  padding: 30rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.field-group {
  margin-top: 22rpx;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.field-label {
  margin-bottom: 10rpx;
  color: #596372;
  font-size: 23rpx;
  font-weight: 800;
}

.field-hint {
  margin: -2rpx 0 14rpx;
  color: #667085;
  font-size: 22rpx;
  font-weight: 700;
}

.form-input,
.picker-shell,
.form-textarea {
  box-sizing: border-box;
  width: 100%;
  border: 2rpx solid rgba(40, 124, 49, 0.22);
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #111827;
  font-size: 25rpx;
  font-weight: 800;
}

.form-input,
.picker-shell {
  height: 72rpx;
  padding: 0 20rpx;
}

.form-input[disabled],
.form-textarea[disabled],
.picker-shell.disabled {
  background: rgba(238, 244, 236, 0.72);
  color: #667085;
}

.picker-shell {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-arrow-icon {
  width: 22rpx;
  height: 22rpx;
  transform: rotate(180deg);
}

.form-textarea {
  min-height: 142rpx;
  padding: 18rpx 20rpx;
  line-height: 1.5;
}

.placeholder {
  color: #9299a3;
}

.selected-medicine-tag {
  box-sizing: border-box;
  min-height: 72rpx;
  padding: 12rpx 14rpx 12rpx 22rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.28);
  border-radius: 22rpx;
  background: #e4f6dd;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.tag-name {
  min-width: 0;
  flex: 1;
  color: #237a2f;
  font-size: 26rpx;
  font-weight: 900;
}

.tag-remove {
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  background: rgba(35, 122, 47, 0.16);
  color: #237a2f;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 42rpx;
}

.catalog-suggestion-list {
  max-height: 360rpx;
  margin-top: 14rpx;
  overflow-y: auto;
  border-radius: 22rpx;
}

.catalog-suggestion-card,
.holder-suggestion-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 112rpx;
  padding: 16rpx;
  border-radius: 20rpx;
  background: #edf4ff;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 16rpx;
  text-align: left;
}

.catalog-suggestion-card + .catalog-suggestion-card,
.holder-suggestion-card + .holder-suggestion-card {
  margin-top: 12rpx;
}

.holder-suggestion-list {
  max-height: 340rpx;
  margin-top: 14rpx;
  overflow-y: auto;
  border-radius: 22rpx;
}

.readonly-holder {
  box-sizing: border-box;
  width: 100%;
  min-height: 72rpx;
  padding: 16rpx 20rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.16);
  border-radius: 20rpx;
  background: rgba(238, 244, 236, 0.72);
  color: #111827;
  font-size: 25rpx;
  font-weight: 900;
}

.holder-hint {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  font-weight: 700;
}

.suggestion-cover {
  width: 78rpx;
  height: 78rpx;
  flex: 0 0 78rpx;
  border-radius: 18rpx;
  background: #f4fbef;
}

.suggestion-copy {
  min-width: 0;
  flex: 1;
}

.suggestion-name {
  color: #111827;
  font-size: 27rpx;
  font-weight: 900;
}

.suggestion-meta,
.suggestion-category,
.hint-line {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  font-weight: 700;
}

.medicine-photo-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18rpx;
}

.medicine-photo-card,
.medicine-photo,
.photo-upload {
  width: 150rpx;
  height: 150rpx;
  border-radius: 22rpx;
}

.medicine-photo-card {
  position: relative;
}

.medicine-photo {
  overflow: hidden;
  background: #f4fbef;
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
  font-size: 28rpx;
  font-weight: 900;
  line-height: 142rpx;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 20rpx;
}

.ghost-action,
.primary-action {
  height: 92rpx;
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

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
