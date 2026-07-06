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
            <text class="eyebrow">{{ medicine.category?.name || "未分类药品" }}</text>
            <view class="title-row">
              <text class="page-title-text">{{ medicine.name }}</text>
              <text class="stock-pill" :class="getMedicineStockClass(medicine.stock_status)">
                {{ medicine.stock_status_label }}
              </text>
            </view>
            <text class="desc-text">
              {{ medicine.description || medicine.usage_notes || "暂无药品说明" }}
            </text>
          </view>

          <view class="info-panel">
            <view class="info-section">
              <text class="info-label">当前总库存</text>
              <text class="info-value">
                {{ formatMedicineQuantity(medicine.total_current_quantity, medicine.unit) }}
              </text>
            </view>
            <view class="info-divider" />
            <view class="info-section">
              <text class="info-label">累计入库</text>
              <text class="info-value">
                {{ formatMedicineQuantity(medicine.total_in_quantity, medicine.unit) }}
              </text>
            </view>
            <view class="info-divider" />
            <view class="info-section">
              <text class="info-label">规格</text>
              <text class="info-value">{{ medicine.specification || "暂无规格" }}</text>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">持有人库存</text>
              <text class="section-meta">{{ medicine.holder_count }} 位</text>
            </view>
            <view v-if="medicine.holders.length" class="holder-list">
              <button
                v-for="holder in medicine.holders"
                :key="holder.holding_id"
                class="holder-card"
                :class="{ mine: holder.is_current_user_holder }"
                hover-class="button-hover"
                @tap="goHoldingDetail(holder.holding_id)"
              >
                <view>
                  <text class="holder-name">{{ holder.holder_nickname }}</text>
                  <text class="holder-meta">
                    {{ holder.is_current_user_holder ? "我持有" : "协会成员持有" }}
                  </text>
                </view>
                <text class="holder-quantity">
                  {{ formatMedicineQuantity(holder.current_quantity, holder.unit) }}
                </text>
              </button>
            </view>
            <text v-else class="empty-line">暂无持有人库存</text>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">药品动态</text>
              <text class="section-meta">最近记录</text>
            </view>
            <view v-if="medicine.recent_logs.length" class="dynamic-list">
              <view
                v-for="log in medicine.recent_logs"
                :key="log.id"
                class="medicine-dynamic-card"
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
            <text v-else class="empty-line">暂无药品动态</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";

import { getMedicineDetail, type MedicineDetailDto } from "@/api/medicines";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  formatMedicineQuantity,
  getMedicineOperationLabel,
  getMedicineStockClass,
} from "@/pages/medicines/medicine-page";

import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const medicineId = ref("");
const medicine = ref<MedicineDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");

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
.holder-card {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button::after,
.retry-button::after,
.holder-card::after {
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
.empty-line,
.holder-name,
.holder-meta,
.holder-quantity,
.dynamic-title,
.dynamic-subtitle,
.dynamic-desc {
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
  margin-top: 34rpx;
}

.eyebrow {
  color: #6f7a65;
  font-size: 24rpx;
  font-weight: 800;
}

.title-row,
.section-head,
.dynamic-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.title-row {
  margin-top: 12rpx;
}

.page-title-text {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.stock-pill {
  flex-shrink: 0;
  padding: 9rpx 14rpx;
  border-radius: 14rpx;
  font-size: 22rpx;
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
  margin-top: 26rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.info-panel {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  overflow: hidden;
}

.info-section {
  padding: 26rpx 20rpx;
}

.info-divider {
  width: 1rpx;
  margin: 26rpx 0;
  background: rgba(189, 214, 185, 0.72);
}

.info-label,
.section-meta,
.empty-line,
.holder-meta,
.dynamic-subtitle {
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
  padding: 30rpx;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.holder-list,
.dynamic-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.holder-card {
  box-sizing: border-box;
  min-height: 94rpx;
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: #edf4ff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.holder-card.mine {
  background: #e4f6dd;
}

.holder-name {
  color: #111827;
  font-size: 27rpx;
  font-weight: 900;
}

.holder-quantity {
  color: #287c31;
  font-size: 26rpx;
  font-weight: 900;
}

.medicine-dynamic-card {
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f4fbef;
}

.dynamic-title,
.dynamic-quantity {
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
}

.dynamic-desc {
  margin-top: 12rpx;
  color: #4b5563;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1.45;
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
  background: #e8f5e6;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 64rpx;
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
