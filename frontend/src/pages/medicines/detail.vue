<template>
  <view class="medicine-detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">药品详情</text>
            <text class="nav-subtitle">库存、持有人与药品动态</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载药品详情</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">药品详情加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
          <button class="retry-button" hover-class="button-hover" @tap="loadMedicineDetail">
            重新加载
          </button>
        </view>

        <view v-else-if="medicine" class="detail-content">
          <view class="hero-card">
            <image
              v-if="medicine.cover_image_url"
              class="hero-image"
              :src="medicine.cover_image_url"
              mode="aspectFill"
            />
            <view v-else class="hero-placeholder">
              <image class="hero-placeholder-icon" :src="medicineIcon" mode="aspectFit" />
            </view>
          </view>

          <view class="title-block">
            <view class="category-row">
              <text
                class="category-tag"
                :class="getMedicineCategoryClass(medicine.category?.name)"
              >
                {{ medicine.category?.name || MEDICINE_DEFAULT_CATEGORY_NAME }}
              </text>
              <text class="stock-pill" :class="getMedicineStockClass(medicine.stock_status)">
                {{ medicine.stock_status_label }}
              </text>
            </view>
            <view class="title-row">
              <text class="page-title-text">{{ medicine.name }}</text>
              <button
                v-if="medicine.permissions.can_edit_catalog"
                class="edit-button"
                hover-class="button-hover"
                @tap="openEditCatalogModal"
              >
                编辑
              </button>
            </view>
          </view>

          <view class="medicine-info-panel">
            <view class="holder-section">
              <view class="section-head">
                <text class="section-title">持有人库存</text>
                <text class="section-meta">{{ medicine.holder_count }} 位</text>
              </view>
              <scroll-view
                v-if="medicine.holders.length"
                class="holder-strip"
                scroll-x
                :show-scrollbar="false"
              >
                <view class="holder-row">
                  <button
                    v-for="holder in medicine.holders"
                    :key="holder.holding_id"
                    class="holder-inventory-card"
                    :class="{ mine: holder.is_current_user_holder }"
                    hover-class="button-hover"
                    @tap="goHoldingDetail(holder.holding_id)"
                  >
                    <text class="holder-card-name">{{ holder.holder_nickname }}</text>
                    <text class="holder-card-quantity">
                      {{ formatMedicineQuantity(holder.current_quantity, holder.unit) }}
                    </text>
                  </button>
                </view>
              </scroll-view>
              <text v-else class="empty-line">暂无持有人库存</text>
            </view>

            <view class="info-divider" />

            <view class="catalog-section">
              <text class="section-title">药品信息</text>
              <view class="info-grid">
                <view class="info-item">
                  <text class="info-label">类型</text>
                  <text class="info-value">
                    {{ medicine.category?.name || MEDICINE_DEFAULT_CATEGORY_NAME }}
                  </text>
                </view>
                <view class="info-item">
                  <text class="info-label">规格</text>
                  <text class="info-value">{{ medicine.specification || "暂无规格" }}</text>
                </view>
                <view class="info-item">
                  <text class="info-label">库存</text>
                  <text class="info-value">
                    {{ formatMedicineQuantity(medicine.total_current_quantity, medicine.unit) }}
                  </text>
                </view>
              </view>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">药品说明</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">功能主治</text>
              <text class="section-line-value">{{ medicine.description || "暂无药品说明" }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">注意事项</text>
              <text class="section-line-value">{{ medicine.usage_notes || "暂无注意事项" }}</text>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">药品动态</text>
              <text class="section-meta">{{ medicine.recent_logs.length }}</text>
            </view>
            <view class="filter-row">
              <button
                v-for="option in logFilterOptions"
                :key="option.value"
                class="filter-button"
                :class="{ active: logFilter === option.value }"
                hover-class="button-hover"
                @tap="changeLogFilter(option.value)"
              >
                {{ option.label }}
              </button>
            </view>
            <scroll-view class="records-scroll" scroll-y :show-scrollbar="false">
              <view v-if="filteredRecentLogs.length" class="dynamic-list">
                <view
                  v-for="log in filteredRecentLogs"
                  :key="log.id"
                  class="medicine-dynamic-card"
                  :class="getMedicineLogToneClass(log.operation_type)"
                >
                  <view class="dynamic-head">
                    <view>
                      <text class="dynamic-title">
                        {{ getMedicineOperationLabel(log.operation_type) }}
                      </text>
                      <text class="dynamic-subtitle">
                        {{ log.operator?.nickname || "系统" }} · {{ formatMedicineTime(log.created_at) }}
                      </text>
                    </view>
                    <button
                      class="dynamic-view-button"
                      hover-class="button-hover"
                      @tap="openLogModal(log)"
                    >
                      查看详情
                    </button>
                  </view>
                  <text class="dynamic-summary">
                    {{ getLogSummary(log) }}
                  </text>
                </view>
              </view>
              <text v-else class="empty-line">暂无药品动态</text>
            </scroll-view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="viewingLog" class="modal-mask" @tap="closeLogModal">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">药品动态详情</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeLogModal">×</button>
        </view>
        <text class="modal-hint">{{ formatMedicineTime(viewingLog.created_at) }}</text>
        <view class="modal-detail-grid">
          <view class="modal-detail-row">
            <text class="modal-detail-label">动态</text>
            <text class="modal-detail-value">
              {{ getMedicineOperationLabel(viewingLog.operation_type) }}
            </text>
          </view>
          <view class="modal-detail-row">
            <text class="modal-detail-label">操作人</text>
            <text class="modal-detail-value">
              {{ viewingLog.operator?.nickname || "系统" }}
            </text>
          </view>
          <view class="modal-detail-row">
            <text class="modal-detail-label">数量变化</text>
            <text class="modal-detail-value">
              {{ formatMedicineQuantity(viewingLog.quantity_delta, viewingLog.unit) }}
            </text>
          </view>
          <view class="modal-detail-row">
            <text class="modal-detail-label">变更前</text>
            <text class="modal-detail-value">
              {{ formatMedicineQuantity(viewingLog.quantity_before, viewingLog.unit) }}
            </text>
          </view>
          <view class="modal-detail-row">
            <text class="modal-detail-label">变更后</text>
            <text class="modal-detail-value">
              {{ formatMedicineQuantity(viewingLog.quantity_after, viewingLog.unit) }}
            </text>
          </view>
        </view>
        <text class="modal-record-remark">
          {{ getLogSummary(viewingLog) }}
        </text>
      </view>
    </view>

    <view v-if="editCatalogVisible" class="modal-mask" @tap="closeEditCatalogModal">
      <view class="modal-panel edit-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">编辑药品</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeEditCatalogModal">×</button>
        </view>
        <view class="edit-form">
          <view class="field-group">
            <text class="field-label">药品名称</text>
            <input
              v-model.trim="editDraft.name"
              class="form-input"
              placeholder="药品名称"
              placeholder-class="placeholder"
            />
          </view>
          <view class="field-group">
            <text class="field-label">药品类型</text>
            <picker
              :range="editCategoryOptions"
              range-key="label"
              :value="selectedEditCategoryIndex"
              @change="handleEditCategoryChange"
            >
              <view class="picker-shell">
                <text>{{ selectedEditCategoryLabel }}</text>
              </view>
            </picker>
            <input
              v-if="isEditCustomCategory"
              v-model.trim="editDraft.category_name"
              class="form-input category-custom-input"
              placeholder="请输入自定义类型"
              placeholder-class="placeholder"
            />
          </view>
          <view class="field-grid">
            <view class="field-group">
              <text class="field-label">规格</text>
              <input
                v-model.trim="editDraft.specification"
                class="form-input"
                placeholder="250mg/片"
                placeholder-class="placeholder"
              />
            </view>
            <view class="field-group">
              <text class="field-label">单位</text>
              <input
                v-model.trim="editDraft.unit"
                class="form-input"
                placeholder="片 / 支 / 瓶"
                placeholder-class="placeholder"
              />
            </view>
          </view>
          <view class="field-group">
            <text class="field-label">功能主治</text>
            <textarea
              v-model.trim="editDraft.description"
              class="form-textarea"
              maxlength="500"
              placeholder="用途、适用场景"
              placeholder-class="placeholder"
            />
          </view>
          <view class="field-group">
            <text class="field-label">注意事项</text>
            <textarea
              v-model.trim="editDraft.usage_notes"
              class="form-textarea"
              maxlength="500"
              placeholder="剂量、禁忌、需线下确认事项"
              placeholder-class="placeholder"
            />
          </view>
        </view>
        <button
          class="modal-submit"
          :loading="isSubmittingEdit"
          hover-class="button-hover"
          @tap="submitCatalogEdit"
        >
          保存修改
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import {
  getMedicineCategories,
  getMedicineDetail,
  updateMedicineCatalog,
  type MedicineCatalogUpdatePayload,
  type MedicineCategoryDto,
  type MedicineDetailDto,
  type MedicineStockLogDto,
} from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  MEDICINE_DEFAULT_CATEGORY_NAME,
  MEDICINE_LOG_FILTER_OPTIONS,
  formatMedicineQuantity,
  getMedicineCategoryClass,
  getMedicineLogToneClass,
  getMedicineOperationLabel,
  getMedicineStockClass,
  isMedicineLogVisibleForFilter,
  type MedicineLogFilterValue,
} from "@/pages/medicines/medicine-page";

import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";
type PickerChangeEvent = { detail: { value: string | number } };
const EDIT_CUSTOM_CATEGORY_VALUE = "__custom__";
type EditDraft = {
  name: string;
  category_id: string;
  category_name: string;
  specification: string;
  unit: string;
  description: string;
  usage_notes: string;
  cover_image_url: string;
};

const userStore = useUserStore();
const medicineId = ref("");
const medicine = ref<MedicineDetailDto | null>(null);
const categories = ref<MedicineCategoryDto[]>([]);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const logFilter = ref<MedicineLogFilterValue>("all");
const viewingLog = ref<MedicineStockLogDto | null>(null);
const editCatalogVisible = ref(false);
const isSubmittingEdit = ref(false);
const isEditCustomCategory = ref(false);
const editDraft = ref<EditDraft>({
  name: "",
  category_id: "",
  category_name: "",
  specification: "",
  unit: "",
  description: "",
  usage_notes: "",
  cover_image_url: "",
});
const logFilterOptions = MEDICINE_LOG_FILTER_OPTIONS;

const filteredRecentLogs = computed(() =>
  (medicine.value?.recent_logs || []).filter((log) =>
    isMedicineLogVisibleForFilter(log.operation_type, logFilter.value),
  ),
);
const editCategoryOptions = computed(() => [
  { label: "其他（默认）", value: "" },
  ...categories.value.map((category) => ({
    label: category.name,
    value: category.id,
  })),
  { label: "自定义", value: EDIT_CUSTOM_CATEGORY_VALUE },
]);
const selectedEditCategoryIndex = computed(() =>
  Math.max(
    editCategoryOptions.value.findIndex(
      (option) =>
        option.value ===
        (isEditCustomCategory.value
          ? EDIT_CUSTOM_CATEGORY_VALUE
          : editDraft.value.category_id),
    ),
    0,
  ),
);
const selectedEditCategoryLabel = computed(
  () => editCategoryOptions.value[selectedEditCategoryIndex.value]?.label || "其他（默认）",
);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function loadMedicineDetail() {
  const token = await getAccessToken();
  if (!token || !medicineId.value) {
    loadState.value = "error";
    errorMessage.value = "缺少药品 ID";
    return;
  }

  loadState.value = "loading";
  errorMessage.value = "";
  try {
    medicine.value = await getMedicineDetail(token, medicineId.value);
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

async function loadCategories() {
  if (categories.value.length) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  try {
    const data = await getMedicineCategories(token);
    categories.value = data.items;
  } catch (error) {
    const message = error instanceof Error ? error.message : "分类加载失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

function pickerIndex(event: PickerChangeEvent): number {
  return Number(event.detail.value) || 0;
}

function formatMedicineTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(
    2,
    "0",
  )}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function getLogSummary(log: MedicineStockLogDto): string {
  if (log.description) {
    return log.description;
  }
  if (log.reason_text) {
    return log.reason_text;
  }
  return `${getMedicineOperationLabel(log.operation_type)} ${formatMedicineQuantity(
    log.quantity_delta,
    log.unit,
  )}`;
}

function changeLogFilter(value: MedicineLogFilterValue) {
  logFilter.value = value;
}

function openLogModal(log: MedicineStockLogDto) {
  viewingLog.value = log;
}

function closeLogModal() {
  viewingLog.value = null;
}

async function openEditCatalogModal() {
  if (!medicine.value) {
    return;
  }
  await loadCategories();
  editDraft.value = {
    name: medicine.value.name,
    category_id: medicine.value.category?.id || "",
    category_name: "",
    specification: medicine.value.specification || "",
    unit: medicine.value.unit,
    description: medicine.value.description || "",
    usage_notes: medicine.value.usage_notes || "",
    cover_image_url: medicine.value.cover_image_url || "",
  };
  isEditCustomCategory.value = false;
  editCatalogVisible.value = true;
}

function closeEditCatalogModal() {
  if (!isSubmittingEdit.value) {
    editCatalogVisible.value = false;
  }
}

function handleEditCategoryChange(event: PickerChangeEvent) {
  const selectedValue = editCategoryOptions.value[pickerIndex(event)]?.value || "";
  isEditCustomCategory.value = selectedValue === EDIT_CUSTOM_CATEGORY_VALUE;
  editDraft.value.category_id = isEditCustomCategory.value ? "" : selectedValue;
  if (!isEditCustomCategory.value) {
    editDraft.value.category_name = "";
  }
}

function buildEditPayload(): MedicineCatalogUpdatePayload {
  const customCategory = editDraft.value.category_name.trim();
  const payload: MedicineCatalogUpdatePayload = {
    name: editDraft.value.name.trim(),
    specification: editDraft.value.specification.trim() || null,
    unit: editDraft.value.unit.trim(),
    description: editDraft.value.description.trim() || null,
    usage_notes: editDraft.value.usage_notes.trim() || null,
    cover_image_url: editDraft.value.cover_image_url.trim() || null,
  };
  if (isEditCustomCategory.value) {
    payload.category_name = customCategory || MEDICINE_DEFAULT_CATEGORY_NAME;
  } else if (customCategory) {
    payload.category_name = customCategory;
  } else if (editDraft.value.category_id) {
    payload.category_id = editDraft.value.category_id;
  } else {
    payload.category_name = MEDICINE_DEFAULT_CATEGORY_NAME;
  }
  return payload;
}

async function submitCatalogEdit() {
  if (!medicine.value || isSubmittingEdit.value) {
    return;
  }
  if (!editDraft.value.name.trim()) {
    uni.showToast({ title: "请输入药品名称", icon: "none" });
    return;
  }
  if (!editDraft.value.unit.trim()) {
    uni.showToast({ title: "请输入计量单位", icon: "none" });
    return;
  }
  if (isEditCustomCategory.value && !editDraft.value.category_name.trim()) {
    uni.showToast({ title: "请输入自定义类型", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isSubmittingEdit.value = true;
  try {
    await updateMedicineCatalog(token, medicine.value.medicine_id, buildEditPayload());
    uni.showToast({ title: "药品已更新", icon: "success" });
    editCatalogVisible.value = false;
    await loadMedicineDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmittingEdit.value = false;
  }
}

function goHoldingDetail(holdingId: string) {
  uni.navigateTo({ url: `/pages/medicines/holding?holding_id=${holdingId}` });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  medicineId.value = typeof query?.medicine_id === "string" ? query.medicine_id : "";
  void loadMedicineDetail();
});
</script>

<style scoped>
.medicine-detail-page {
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
    calc(env(safe-area-inset-bottom) + 44rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button,
.retry-button,
.edit-button,
.holder-inventory-card,
.filter-button,
.dynamic-view-button,
.modal-close,
.modal-submit {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.retry-button::after,
.edit-button::after,
.holder-inventory-card::after,
.filter-button::after,
.dynamic-view-button::after,
.modal-close::after,
.modal-submit::after {
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
.state-title,
.state-copy,
.page-title-text,
.section-title,
.section-meta,
.empty-line,
.holder-card-name,
.holder-card-quantity,
.info-label,
.info-value,
.section-line,
.section-line-label,
.section-line-value,
.dynamic-title,
.dynamic-subtitle,
.dynamic-summary,
.modal-title,
.modal-hint,
.modal-record-remark,
.field-label {
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

.detail-content {
  margin-top: 38rpx;
}

.hero-card,
.hero-image,
.hero-placeholder {
  width: 100%;
  height: 340rpx;
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
  margin-top: 32rpx;
}

.category-row,
.title-row,
.section-head,
.dynamic-head,
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.category-row {
  justify-content: flex-start;
}

.category-tag,
.stock-pill {
  padding: 9rpx 14rpx;
  border-radius: 14rpx;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 1;
}

.category-antibiotic {
  background: #dff1ff;
  color: #1d6fb8;
}

.category-painkiller {
  background: #fff0d9;
  color: #a45b00;
}

.category-deworming {
  background: #e4f6dd;
  color: #237a2f;
}

.category-disinfection {
  background: #def7f0;
  color: #167766;
}

.category-eye-ear {
  background: #ffe6e6;
  color: #c43b3b;
}

.category-nutrition {
  background: #f3e8ff;
  color: #7a3eb1;
}

.category-other {
  background: #edf0f3;
  color: #526070;
}

.title-row {
  margin-top: 14rpx;
  align-items: flex-start;
}

.page-title-text {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.edit-button,
.retry-button {
  background: #e8f5e6;
  color: #287c31;
  font-weight: 900;
}

.edit-button {
  flex: 0 0 104rpx;
  height: 56rpx;
  border-radius: 18rpx;
  font-size: 24rpx;
  line-height: 56rpx;
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

.medicine-info-panel,
.section-card,
.state-box {
  box-sizing: border-box;
  margin-top: 26rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.medicine-info-panel {
  overflow: hidden;
  border: 2rpx solid rgba(212, 237, 208, 0.72);
}

.holder-section,
.catalog-section,
.section-card,
.state-box {
  padding: 30rpx;
}

.holder-section {
  background: rgba(247, 252, 246, 0.78);
}

.catalog-section {
  background: rgba(255, 255, 255, 0.68);
}

.info-divider {
  height: 1rpx;
  margin: 0 30rpx;
  background: rgba(189, 214, 185, 0.72);
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.section-meta,
.empty-line,
.dynamic-subtitle {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.holder-strip {
  width: 100%;
  margin-top: 20rpx;
  overflow: hidden;
  white-space: nowrap;
}

.holder-row {
  display: flex;
  gap: 12rpx;
}

.holder-inventory-card {
  box-sizing: border-box;
  min-width: 150rpx;
  height: 70rpx;
  padding: 9rpx 16rpx;
  border-radius: 14rpx;
  background: #edf4ff;
  color: #2276ff;
  text-align: left;
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  gap: 5rpx;
  flex-shrink: 0;
}

.holder-inventory-card.mine {
  background: #e4f6dd;
  color: #237a2f;
}

.holder-card-name,
.holder-card-quantity {
  overflow: hidden;
  font-weight: 900;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.holder-card-name {
  font-size: 20rpx;
}

.holder-card-quantity {
  font-size: 18rpx;
}

.info-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx;
}

.info-item {
  min-height: 86rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(244, 251, 239, 0.78);
}

.info-label {
  color: #788293;
  font-size: 22rpx;
  font-weight: 800;
}

.info-value {
  margin-top: 10rpx;
  color: #273040;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.35;
}

.section-line {
  margin-top: 18rpx;
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  line-height: 1.55;
}

.section-line-label {
  flex: 0 0 96rpx;
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

.filter-row {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.filter-button {
  height: 56rpx;
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

.dynamic-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.medicine-dynamic-card {
  box-sizing: border-box;
  padding: 22rpx;
  border-radius: 22rpx;
}

.log-use {
  background: #ffe8e8;
  border: 2rpx solid rgba(215, 53, 70, 0.24);
}

.log-purchase {
  background: #edf8e8;
  border: 2rpx solid rgba(91, 177, 86, 0.28);
}

.log-other {
  background: #fff4dc;
  border: 2rpx solid rgba(210, 145, 28, 0.22);
}

.dynamic-title {
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.dynamic-subtitle {
  margin-top: 8rpx;
}

.dynamic-view-button {
  width: 142rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #287c31;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.dynamic-summary {
  margin-top: 18rpx;
  padding: 16rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.56);
  color: #273040;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1.45;
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
  max-height: 84vh;
  padding: 30rpx 30rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -18rpx 46rpx rgba(17, 24, 39, 0.18);
}

.edit-panel {
  overflow-y: auto;
}

.modal-title {
  color: #111827;
  font-size: 34rpx;
  font-weight: 900;
}

.modal-close {
  width: 58rpx;
  height: 58rpx;
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

.modal-detail-grid {
  margin-top: 22rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.modal-detail-row {
  display: grid;
  grid-template-columns: 126rpx minmax(0, 1fr);
  gap: 16rpx;
}

.modal-detail-label {
  color: #788293;
  font-size: 24rpx;
  font-weight: 800;
}

.modal-detail-value {
  color: #273040;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.45;
}

.modal-record-remark {
  margin-top: 22rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: #f4fbef;
  color: #273040;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1.5;
}

.edit-form {
  margin-top: 22rpx;
}

.field-group {
  margin-top: 20rpx;
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

.picker-shell {
  display: flex;
  align-items: center;
}

.category-custom-input {
  margin-top: 14rpx;
}

.form-textarea {
  min-height: 132rpx;
  padding: 18rpx 20rpx;
  line-height: 1.5;
}

.placeholder {
  color: #9299a3;
}

.modal-submit {
  width: 100%;
  height: 84rpx;
  margin-top: 24rpx;
  border-radius: 26rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 84rpx;
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

.retry-button {
  width: 168rpx;
  height: 64rpx;
  margin-top: 22rpx;
  border-radius: 20rpx;
  font-size: 25rpx;
  line-height: 64rpx;
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
