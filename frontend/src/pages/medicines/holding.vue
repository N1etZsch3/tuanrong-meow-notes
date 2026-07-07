<template>
  <view class="holding-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="holding-scroll" scroll-y :show-scrollbar="false">
      <view class="holding-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">库存详情</text>
            <text class="nav-subtitle">持有人库存与用药申请</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载库存详情</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">库存详情加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
          <button class="retry-button" hover-class="button-hover" @tap="loadMedicineHoldingDetail">
            重新加载
          </button>
        </view>

        <view v-else-if="holding" class="detail-content">
          <view class="hero-card">
            <image
              v-if="holding.medicine.cover_image_url"
              class="hero-image"
              :src="holding.medicine.cover_image_url"
              mode="aspectFill"
            />
            <view v-else class="hero-icon-shell">
              <image class="hero-icon" :src="medicineIcon" mode="aspectFit" />
            </view>
            <view class="hero-copy">
              <text class="eyebrow">{{ holding.medicine.category_name || "其他" }}</text>
              <text class="page-title-text">{{ holding.medicine.name }}</text>
              <text class="desc-text">
                {{ holding.medicine.specification || "暂无规格" }} ·
                {{ holding.holder.nickname }} 持有
              </text>
            </view>
          </view>

          <view class="info-panel">
            <view class="info-section">
              <text class="info-label">当前库存</text>
              <text class="info-value">
                {{ formatMedicineQuantity(holding.current_quantity, holding.unit) }}
              </text>
            </view>
            <view class="info-section">
              <text class="info-label">累计入库</text>
              <text class="info-value">
                {{ formatMedicineQuantity(holding.total_in_quantity, holding.unit) }}
              </text>
            </view>
            <view class="info-section">
              <text class="info-label">状态</text>
              <text class="info-value">{{ getHoldingStatusLabel(holding.status) }}</text>
            </view>
          </view>

          <view v-if="holding.pending_applications.length" class="section-card">
            <view class="section-head">
              <text class="section-title">待处理申请</text>
              <text class="section-meta">{{ holding.pending_applications.length }}</text>
            </view>
            <view class="application-list">
              <view
                v-for="application in holding.pending_applications"
                :key="application.id"
                class="application-card"
              >
                <view>
                  <text class="application-title">
                    申请 {{ formatMedicineQuantity(application.quantity, application.unit) }}
                  </text>
                  <text class="application-subtitle">{{ application.reason_text }}</text>
                </view>
                <button
                  v-if="holding.permissions.can_review_application"
                  class="approve-button"
                  hover-class="button-hover"
                  @tap="approveApplication(application.id)"
                >
                  通过申请
                </button>
              </view>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">库存动态</text>
              <text class="section-meta">最近记录</text>
            </view>
            <view v-if="holding.recent_logs.length" class="dynamic-list">
              <view
                v-for="log in holding.recent_logs"
                :key="log.id"
                class="dynamic-card"
                :class="getMedicineLogToneClass(log.operation_type)"
              >
                <view class="dynamic-head">
                  <text class="dynamic-title">{{ getMedicineOperationLabel(log.operation_type) }}</text>
                  <text class="dynamic-quantity">
                    {{ formatMedicineQuantity(log.quantity_delta, log.unit) }}
                  </text>
                </view>
                <text class="dynamic-subtitle">
                  {{ log.operator?.nickname || "系统" }} · {{ formatMedicineTime(log.created_at) }}
                </text>
                <text v-if="log.reason_text || log.description" class="dynamic-desc">
                  {{ log.reason_text || log.description }}
                </text>
              </view>
            </view>
            <text v-else class="empty-line">暂无库存动态</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="holding" class="bottom-actions">
      <button
        v-if="holding.permissions.can_record"
        class="ghost-action"
        hover-class="button-hover"
        @tap="openOperationForm('purchase')"
      >
        记录购入
      </button>
      <button
        v-if="holding.permissions.can_record"
        class="ghost-action"
        hover-class="button-hover"
        @tap="openOperationForm('scrap')"
      >
        记录报废
      </button>
      <button
        v-if="holding.permissions.can_record"
        class="primary-action"
        hover-class="button-hover"
        @tap="openOperationForm('use')"
      >
        记录使用
      </button>
      <button
        v-else-if="holding.permissions.can_apply"
        class="primary-action wide"
        hover-class="button-hover"
        @tap="openOperationForm('application')"
      >
        申请使用
      </button>
    </view>

    <view v-if="operationFormVisible" class="modal-mask" @tap="closeOperationForm">
      <view class="modal-panel" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">{{ operationTitle }}</text>
          <button class="modal-close" hover-class="button-hover" @tap="closeOperationForm">×</button>
        </view>
        <text class="modal-hint">请填写数量和用途说明，系统会同步生成库存流水。</text>
        <view class="field-group">
          <text class="field-label">数量</text>
          <input
            v-model="operationForm.quantity"
            class="form-input"
            type="digit"
            placeholder="0"
            placeholder-class="placeholder"
          />
        </view>
        <view v-if="operationKind !== 'purchase'" class="field-group">
          <text class="field-label">原因说明</text>
          <textarea
            v-model.trim="operationForm.reason_text"
            class="form-textarea"
            maxlength="300"
            placeholder="说明使用、报废或申请原因"
            placeholder-class="placeholder"
          />
        </view>
        <view class="field-group">
          <text class="field-label">备注</text>
          <input
            v-model.trim="operationForm.remark"
            class="form-input"
            placeholder="可不填"
            placeholder-class="placeholder"
          />
        </view>
        <button
          class="modal-submit"
          :loading="isSubmittingOperation"
          hover-class="button-hover"
          @tap="submitOperation"
        >
          提交
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";

import {
  approveMedicineApplication,
  createMedicineApplication,
  getMedicineHoldingDetail,
  recordMedicinePurchase,
  recordMedicineScrap,
  recordMedicineUse,
  type MedicineHoldingDetailDto,
} from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  getMedicineHoldingStatusLabel as getHoldingStatusLabel,
  getMedicineLogToneClass,
  formatMedicineQuantity,
  getMedicineOperationLabel,
  createDefaultMedicineOperationDraft,
  validateMedicineOperationDraft,
  type MedicineOperationKind,
} from "@/pages/medicines/medicine-page";

import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";
const userStore = useUserStore();
const holdingId = ref("");
const holding = ref<MedicineHoldingDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const operationFormVisible = ref(false);
const operationKind = ref<MedicineOperationKind>("purchase");
const isSubmittingOperation = ref(false);
const operationForm = reactive(createDefaultMedicineOperationDraft());

const operationTitle = computed(() => {
  if (operationKind.value === "purchase") {
    return "记录购入";
  }
  if (operationKind.value === "use") {
    return "记录使用";
  }
  if (operationKind.value === "scrap") {
    return "记录报废";
  }
  return "申请使用";
});

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function loadMedicineHoldingDetail() {
  const token = await getAccessToken();
  if (!token || !holdingId.value) {
    loadState.value = "error";
    errorMessage.value = "缺少库存 ID";
    return;
  }

  loadState.value = "loading";
  errorMessage.value = "";
  try {
    holding.value = await getMedicineHoldingDetail(token, holdingId.value);
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function openOperationForm(kind: MedicineOperationKind) {
  operationKind.value = kind;
  Object.assign(operationForm, createDefaultMedicineOperationDraft());
  operationFormVisible.value = true;
}

function closeOperationForm() {
  if (isSubmittingOperation.value) {
    return;
  }
  operationFormVisible.value = false;
}

function validateOperationForm(): boolean {
  const result = validateMedicineOperationDraft(
    operationForm,
    operationKind.value,
    holding.value?.current_quantity ?? 0,
  );
  if (!result.valid) {
    uni.showToast({ title: result.message || "请检查表单", icon: "none" });
    return false;
  }
  return true;
}

async function submitOperation() {
  if (!validateOperationForm()) {
    return;
  }
  const token = await getAccessToken();
  if (!token || !holdingId.value || isSubmittingOperation.value) {
    return;
  }

  isSubmittingOperation.value = true;
  try {
    const quantity = Number(operationForm.quantity);
    if (operationKind.value === "purchase") {
      await recordMedicinePurchase(token, holdingId.value, {
        quantity,
        source: operationForm.remark || null,
        remark: operationForm.remark || null,
      });
    } else if (operationKind.value === "use") {
      await recordMedicineUse(token, holdingId.value, {
        quantity,
        reason_type: "free_text",
        reason_text: operationForm.reason_text,
        usage_description: operationForm.remark || null,
      });
    } else if (operationKind.value === "scrap") {
      await recordMedicineScrap(token, holdingId.value, {
        quantity,
        reason_type: "scrap",
        reason_text: operationForm.reason_text,
        remark: operationForm.remark || null,
      });
    } else {
      await createMedicineApplication(token, holdingId.value, {
        quantity,
        reason_type: "free_text",
        reason_text: operationForm.reason_text,
        usage_description: operationForm.remark || null,
      });
    }
    uni.showToast({ title: "已提交", icon: "success" });
    operationFormVisible.value = false;
    await loadMedicineHoldingDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "提交失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmittingOperation.value = false;
  }
}

async function approveApplication(applicationId: string) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  try {
    await approveMedicineApplication(token, applicationId, {
      review_comment: "同意本次用药申请",
    });
    uni.showToast({ title: "申请已通过", icon: "success" });
    await loadMedicineHoldingDetail();
  } catch (error) {
    const message = error instanceof Error ? error.message : "审核失败";
    uni.showToast({ title: message, icon: "none" });
  }
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

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  holdingId.value = typeof query?.holding_id === "string" ? query.holding_id : "";
  void loadMedicineHoldingDetail();
});
</script>

<style scoped>
.holding-page {
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

.holding-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.holding-inner {
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
.retry-button,
.approve-button,
.ghost-action,
.primary-action,
.modal-close,
.modal-submit {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.retry-button::after,
.approve-button::after,
.ghost-action::after,
.primary-action::after,
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
.eyebrow,
.page-title-text,
.desc-text,
.info-label,
.info-value,
.section-title,
.section-meta,
.application-title,
.application-subtitle,
.dynamic-title,
.dynamic-subtitle,
.dynamic-desc,
.empty-line,
.modal-title,
.modal-hint,
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
.info-panel,
.section-card,
.state-box {
  box-sizing: border-box;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.hero-card {
  min-height: 220rpx;
  padding: 28rpx;
  display: grid;
  grid-template-columns: 128rpx minmax(0, 1fr);
  align-items: center;
  gap: 24rpx;
}

.hero-icon-shell,
.hero-image {
  width: 128rpx;
  height: 128rpx;
  border-radius: 28rpx;
  overflow: hidden;
}

.hero-icon-shell {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-icon {
  width: 82rpx;
  height: 82rpx;
}

.eyebrow {
  color: #6f7a65;
  font-size: 23rpx;
  font-weight: 800;
}

.page-title-text {
  margin-top: 10rpx;
  color: #111827;
  font-size: 42rpx;
  font-weight: 900;
  line-height: 1.15;
}

.desc-text {
  margin-top: 12rpx;
  color: #465160;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1.45;
}

.info-panel {
  margin-top: 26rpx;
  padding: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  overflow: hidden;
}

.info-section {
  min-height: 96rpx;
  padding: 18rpx 16rpx;
  border-radius: 20rpx;
  background: #f4fbef;
}

.info-label,
.section-meta,
.application-subtitle,
.dynamic-subtitle,
.empty-line {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.info-value {
  margin-top: 12rpx;
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.section-card,
.state-box {
  margin-top: 26rpx;
  padding: 30rpx;
}

.section-head,
.application-card,
.dynamic-head,
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.application-list,
.dynamic-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.application-card,
.dynamic-card {
  padding: 22rpx;
  border-radius: 22rpx;
}

.application-card,
.log-purchase {
  background: #f4fbef;
}

.log-use {
  background: #fff4cc;
}

.log-other {
  background: #edf4ff;
}

.application-title,
.dynamic-title,
.dynamic-quantity {
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.approve-button {
  width: 136rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.dynamic-desc {
  margin-top: 12rpx;
  color: #4b5563;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1.45;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.ghost-action,
.primary-action {
  height: 88rpx;
  border-radius: 28rpx;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 88rpx;
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

.primary-action.wide {
  grid-column: 1 / -1;
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

.field-group {
  margin-top: 22rpx;
}

.field-label {
  margin-bottom: 10rpx;
  color: #596372;
  font-size: 23rpx;
  font-weight: 800;
}

.form-input,
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

.form-input {
  height: 72rpx;
  padding: 0 20rpx;
}

.form-textarea {
  min-height: 142rpx;
  padding: 18rpx 20rpx;
  line-height: 1.5;
}

.placeholder {
  color: #9299a3;
}

.modal-submit,
.retry-button {
  height: 84rpx;
  border-radius: 26rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 84rpx;
}

.modal-submit {
  width: 100%;
  margin-top: 24rpx;
}

.retry-button {
  width: 168rpx;
  height: 64rpx;
  margin-top: 22rpx;
  font-size: 25rpx;
  line-height: 64rpx;
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
