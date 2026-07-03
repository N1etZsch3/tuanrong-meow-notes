<template>
  <view class="edit-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="edit-inner">
      <view class="page-head">
        <button class="back-button" @tap="goBack">‹</button>
        <view class="head-copy">
          <text class="page-title">编辑点位</text>
          <text class="page-subtitle">修改地图展示与路线信息</text>
        </view>
      </view>

      <view v-if="loadState === 'loading'" class="state-panel">
        <text>正在加载点位...</text>
      </view>

      <view v-else class="form-panel">
        <view class="form-field">
          <text class="field-label">点位名称</text>
          <input v-model.trim="form.name" class="field-input" placeholder="请输入点位名称" />
        </view>
        <view class="form-field">
          <text class="field-label">副标题</text>
          <input v-model.trim="form.subtitle" class="field-input" placeholder="可选" />
        </view>
        <view class="form-field">
          <text class="field-label">点位说明</text>
          <textarea v-model.trim="form.description" class="field-textarea" />
        </view>
        <view class="form-field">
          <text class="field-label">位置名称</text>
          <input v-model.trim="form.location_name" class="field-input" placeholder="例如北门草丛" />
        </view>
        <view class="form-field">
          <text class="field-label">详细位置</text>
          <textarea v-model.trim="form.location_detail" class="field-textarea" />
        </view>
        <view class="form-field">
          <text class="field-label">路线说明</text>
          <textarea v-model.trim="form.route_instruction" class="field-textarea" />
        </view>
        <view class="form-field">
          <text class="field-label">附近地标</text>
          <textarea v-model.trim="form.landmark_hint" class="field-textarea" />
        </view>
        <view class="form-field">
          <text class="field-label">入口提示</text>
          <textarea v-model.trim="form.entrance_hint" class="field-textarea" />
        </view>
        <view class="form-grid">
          <view class="form-field">
            <text class="field-label">可见性</text>
            <picker :range="visibilityOptions" range-key="label" @change="selectVisibility">
              <view class="picker-value">{{ currentVisibilityLabel }}</view>
            </picker>
          </view>
          <view class="form-field">
            <text class="field-label">状态</text>
            <picker :range="statusOptions" range-key="label" @change="selectStatus">
              <view class="picker-value">{{ currentStatusLabel }}</view>
            </picker>
          </view>
        </view>
        <button class="save-button" :disabled="saving" @tap="submitEdit">
          {{ saving ? "保存中..." : "保存点位" }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";

import {
  getAdminMapPoint,
  updateAdminMapPoint,
  type AdminMapPointDto,
  type AdminMapPointUpdatePayload,
} from "@/api/admin-map";
import { useUserStore } from "@/stores/user";

import loadingBackground from "../../../../素材/加载页素材/背景.jpg";

type LoadState = "loading" | "ready" | "error";

const userStore = useUserStore();
const pointId = ref("");
const loadState = ref<LoadState>("loading");
const saving = ref(false);
const form = reactive<AdminMapPointUpdatePayload>({
  name: "",
  subtitle: "",
  description: "",
  location_name: "",
  location_detail: "",
  route_instruction: "",
  landmark_hint: "",
  entrance_hint: "",
  visibility: "public",
  status: "active",
});
const visibilityOptions = [
  { label: "公开", value: "public" },
  { label: "仅管理员", value: "admin_only" },
  { label: "隐藏", value: "hidden" },
];
const statusOptions = [
  { label: "正常", value: "active" },
  { label: "停用", value: "inactive" },
  { label: "归档", value: "archived" },
];
const currentVisibilityLabel = computed(
  () => visibilityOptions.find((item) => item.value === form.visibility)?.label || "公开",
);
const currentStatusLabel = computed(
  () => statusOptions.find((item) => item.value === form.status)?.label || "正常",
);

function applyPoint(point: AdminMapPointDto) {
  form.name = point.name;
  form.subtitle = point.subtitle || "";
  form.description = point.description || "";
  form.location_name = point.location_name || "";
  form.location_detail = point.location_detail || "";
  form.route_instruction = point.route_instruction || "";
  form.landmark_hint = point.landmark_hint || "";
  form.entrance_hint = point.entrance_hint || "";
  form.visibility = point.visibility;
  form.status = point.status;
}

async function getToken() {
  const token = await userStore.ensureFreshAccessToken();
  if (!token) {
    uni.showToast({ title: "请先登录", icon: "none" });
  }
  return token;
}

async function loadPoint() {
  const token = await getToken();
  if (!token || !pointId.value) {
    loadState.value = "error";
    return;
  }
  try {
    applyPoint(await getAdminMapPoint(token, pointId.value));
    loadState.value = "ready";
  } catch {
    loadState.value = "error";
    uni.showToast({ title: "点位加载失败", icon: "none" });
  }
}

function selectVisibility(event: Event) {
  const index = Number((event as CustomEvent<{ value: string }>).detail.value);
  form.visibility = visibilityOptions[index]?.value || "public";
}

function selectStatus(event: Event) {
  const index = Number((event as CustomEvent<{ value: string }>).detail.value);
  form.status = statusOptions[index]?.value || "active";
}

async function submitEdit() {
  if (!form.name?.trim()) {
    uni.showToast({ title: "请填写点位名称", icon: "none" });
    return;
  }
  const token = await getToken();
  if (!token || !pointId.value) {
    return;
  }
  saving.value = true;
  try {
    await updateAdminMapPoint(token, pointId.value, form);
    uni.showToast({ title: "点位已保存", icon: "success" });
    setTimeout(() => uni.navigateBack(), 350);
  } catch {
    uni.showToast({ title: "保存失败", icon: "none" });
  } finally {
    saving.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  pointId.value = typeof query?.point_id === "string" ? query.point_id : "";
  void loadPoint();
});
</script>

<style scoped>
.edit-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: #111827;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
}

.edit-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx) 48rpx;
}

.page-head {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
  margin-bottom: 30rpx;
}

.back-button {
  width: 76rpx;
  height: 76rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  font-size: 46rpx;
  line-height: 70rpx;
}

.back-button::after,
.save-button::after {
  border: 0;
}

.head-copy {
  display: flex;
  flex-direction: column;
  gap: var(--catmap-page-title-subtitle-margin, 14rpx);
}

.page-title {
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.page-subtitle {
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.state-panel,
.form-panel {
  box-sizing: border-box;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 42rpx rgba(31, 60, 34, 0.12);
}

.state-panel {
  padding: 48rpx;
  color: #267b2f;
  font-size: 28rpx;
  font-weight: 900;
  text-align: center;
}

.form-panel {
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.field-label {
  color: #374151;
  font-size: 24rpx;
  font-weight: 900;
}

.field-input,
.field-textarea,
.picker-value {
  box-sizing: border-box;
  width: 100%;
  border: 2rpx solid rgba(39, 123, 47, 0.22);
  border-radius: 18rpx;
  background: rgba(247, 251, 239, 0.88);
  color: #111827;
  font-size: 25rpx;
  font-weight: 700;
}

.field-input,
.picker-value {
  height: 72rpx;
  padding: 0 20rpx;
  line-height: 72rpx;
}

.field-textarea {
  min-height: 120rpx;
  padding: 18rpx 20rpx;
  line-height: 1.45;
}

.save-button {
  height: 78rpx;
  margin: 10rpx 0 0;
  border: 0;
  border-radius: 22rpx;
  background: #267b2f;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
}
</style>
