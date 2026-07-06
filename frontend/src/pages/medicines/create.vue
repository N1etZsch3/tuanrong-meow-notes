<template>
  <view class="medicine-form-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="form-scroll" scroll-y :show-scrollbar="false">
      <view class="form-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">新增药品</text>
            <text class="nav-subtitle">创建主档或新增持有库存</text>
          </view>
        </view>

        <view class="section-card">
          <text class="section-title">建档方式</text>
          <view class="mode-row">
            <button
              v-for="option in modeOptions"
              :key="option.value"
              class="mode-button"
              :class="{ active: draft.mode === option.value }"
              hover-class="button-hover"
              @tap="setMode(option.value)"
            >
              {{ option.label }}
            </button>
          </view>
        </view>

        <view v-if="draft.mode === 'existing'" class="section-card">
          <text class="section-title">选择已有药品</text>
          <view class="search-box">
            <input
              v-model.trim="existingKeyword"
              class="search-input"
              confirm-type="search"
              placeholder="输入药品名搜索已有主档"
              placeholder-class="placeholder"
              @confirm="loadExistingMedicines"
            />
            <button class="search-button" hover-class="button-hover" @tap="loadExistingMedicines">
              搜索
            </button>
          </view>
          <view v-if="existingMedicines.length" class="existing-list">
            <button
              v-for="medicine in existingMedicines"
              :key="medicine.medicine_id"
              class="existing-card"
              :class="{ selected: draft.selected_medicine_id === medicine.medicine_id }"
              hover-class="button-hover"
              @tap="selectExistingMedicine(medicine)"
            >
              <text class="existing-name">{{ medicine.name }}</text>
              <text class="existing-meta">
                {{ medicine.specification || "暂无规格" }} · {{ medicine.unit }}
              </text>
            </button>
          </view>
          <text v-else class="hint-line">输入药品名后，可以复用已有主档。</text>
        </view>

        <view v-else class="section-card">
          <text class="section-title">创建新药品</text>
          <view class="field-group">
            <text class="field-label">药品名称</text>
            <input
              v-model.trim="draft.name"
              class="form-input"
              placeholder="如：阿莫西林"
              placeholder-class="placeholder"
            />
          </view>
          <view class="field-group">
            <text class="field-label">药品分类</text>
            <picker
              :range="categoryOptions"
              range-key="label"
              :value="selectedCategoryIndex"
              @change="handleCategoryChange"
            >
              <view class="picker-shell">
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
                placeholder="250mg/片"
                placeholder-class="placeholder"
              />
            </view>
            <view class="field-group">
              <text class="field-label">计量单位</text>
              <input
                v-model.trim="draft.unit"
                class="form-input"
                placeholder="片 / 支 / 瓶"
                placeholder-class="placeholder"
              />
            </view>
          </view>
          <view class="field-group">
            <text class="field-label">药品说明</text>
            <textarea
              v-model.trim="draft.description"
              class="form-textarea"
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
              maxlength="500"
              placeholder="剂量、禁忌、需线下确认事项"
              placeholder-class="placeholder"
            />
          </view>
        </view>

        <view class="section-card">
          <text class="section-title">持有库存</text>
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

import {
  createMedicine,
  getMedicineCategories,
  searchMedicines,
  type MedicineCatalogPayload,
  type MedicineCategoryDto,
} from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import {
  buildMedicineCreatePayload,
  createDefaultMedicineDraft,
  validateMedicineCreateDraft,
  type MedicineCreateMode,
} from "@/pages/medicines/medicine-page";

import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type PickerChangeEvent = { detail: { value: string | number } };
type SearchMedicineItem = MedicineCatalogPayload & { medicine_id: string };

const userStore = useUserStore();
const draft = ref(createDefaultMedicineDraft());
const categories = ref<MedicineCategoryDto[]>([]);
const existingKeyword = ref("");
const existingMedicines = ref<SearchMedicineItem[]>([]);
const isSubmitting = ref(false);
const modeOptions: Array<{ label: string; value: MedicineCreateMode }> = [
  { label: "创建新药品", value: "new" },
  { label: "选择已有药品", value: "existing" },
];

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
  draft.value.category_id = categoryOptions.value[pickerIndex(event)]?.value || "";
}

function setMode(mode: MedicineCreateMode) {
  draft.value.mode = mode;
  draft.value.selected_medicine_id = "";
}

async function loadExistingMedicines() {
  const keyword = existingKeyword.value.trim();
  if (!keyword) {
    uni.showToast({ title: "请输入药品名", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  const data = await searchMedicines(token, keyword);
  existingMedicines.value = data.items;
}

function selectExistingMedicine(medicine: SearchMedicineItem) {
  draft.value.selected_medicine_id = medicine.medicine_id;
  draft.value.name = medicine.name;
  draft.value.specification = medicine.specification || "";
  draft.value.unit = medicine.unit;
}

async function submitMedicine() {
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
.mode-button,
.search-button,
.existing-card,
.ghost-action,
.primary-action {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.mode-button::after,
.search-button::after,
.existing-card::after,
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
.hint-line,
.existing-name,
.existing-meta {
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

.mode-row {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.mode-button {
  height: 68rpx;
  border-radius: 22rpx;
  background: #eef4ec;
  color: #526070;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 68rpx;
}

.mode-button.active {
  background: #287c31;
  color: #ffffff;
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

.form-input,
.picker-shell,
.form-textarea,
.search-box {
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

.search-box {
  height: 72rpx;
  margin-top: 20rpx;
  padding: 0 12rpx 0 20rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 68rpx;
  color: #111827;
  font-size: 25rpx;
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

.existing-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.existing-card {
  padding: 20rpx;
  border-radius: 20rpx;
  background: #edf4ff;
  color: #111827;
  text-align: left;
}

.existing-card.selected {
  background: #e4f6dd;
  box-shadow: inset 0 0 0 3rpx rgba(40, 124, 49, 0.28);
}

.existing-name {
  font-size: 27rpx;
  font-weight: 900;
}

.existing-meta,
.hint-line {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  font-weight: 700;
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
