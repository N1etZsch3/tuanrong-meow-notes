<template>
  <view class="onboarding-page">
    <view class="background-cat" />
    <view class="page-content">
      <view class="hero">
        <view class="hero-icon">
          <image class="hero-user" :src="initIcon" mode="aspectFit" />
        </view>
        <view class="hero-copy">
          <view class="eyebrow-row">
            <view class="eyebrow-dot" />
            <text class="eyebrow">首次登录</text>
          </view>
          <text class="hero-title">初始化身份</text>
          <text class="hero-subtitle">请完善基础信息后开始使用校园猫协任务系统</text>
        </view>
      </view>

      <view class="form-card">
        <view class="step-pill">步骤 2 / 2</view>

        <view class="field-group">
          <view class="field-label">
            <image class="field-icon" :src="userIcon" mode="aspectFit" />
            <text>昵称</text>
            <text class="required">*</text>
          </view>
          <input
            v-model="form.nickname"
            class="field-input"
            placeholder="请输入昵称"
            placeholder-class="input-placeholder"
            maxlength="20"
          />
        </view>

        <view class="field-group">
          <view class="field-label">
            <image class="field-icon" :src="avatarIcon" mode="aspectFit" />
            <text>头像</text>
          </view>
          <view class="avatar-picker" @tap="chooseAvatar">
            <view class="avatar-shell">
              <image
                class="avatar-image"
                :src="avatarDisplay"
                mode="aspectFit"
                @error="avatarLoadFailed = true"
              />
              <view class="camera-badge">
                <text class="camera-text">+</text>
              </view>
            </view>
            <text class="avatar-copy">点击上传头像</text>
            <text class="avatar-rule">未上传时默认使用萌猫头像，图片不超过 2MB</text>
          </view>
        </view>

        <view class="field-group">
          <view class="field-label">
            <image class="field-icon" :src="departmentIcon" mode="aspectFit" />
            <text>部门</text>
            <text class="required">*</text>
          </view>
          <picker mode="selector" :range="departments" :value="departmentIndex" @change="onDepartmentChange">
            <view class="picker-field">
              <text :class="selectedDepartment ? 'picker-value' : 'picker-placeholder'">
                {{ selectedDepartment || "请选择部门" }}
              </text>
              <text class="picker-arrow">⌄</text>
            </view>
          </picker>
        </view>

        <view class="field-group">
          <view class="field-label">
            <text class="phone-icon">☎</text>
            <text>联系方式</text>
            <text class="required">*</text>
          </view>
          <input
            v-model.trim="form.contact_info"
            class="field-input"
            type="number"
            placeholder="请输入手机号"
            placeholder-class="input-placeholder"
            maxlength="11"
          />
          <view class="privacy-note">
            <image class="privacy-icon" :src="shieldIcon" mode="aspectFit" />
            <text>手机号仅管理员可见，用于任务协作时必要联系。</text>
          </view>
        </view>

        <button class="primary-button" :loading="isSubmitting" @tap="submitProfile">
          完成初始化并进入系统
        </button>
        <text class="card-footnote">后续可在“我的”页面继续修改资料</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { uploadUserAvatar } from "@/api/files";
import { HOME_ROUTE, LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import { normalizeInitialProfileText } from "./complete-page";
import initIcon from "../../../素材/svg/登录页/初始化用户.svg";
import userIcon from "../../../素材/登录页素材/登录.svg";
import avatarIcon from "../../../素材/svg/登录页/头像.svg";
import departmentIcon from "../../../素材/svg/登录页/部门管理.svg";
import shieldIcon from "../../../素材/svg/登录页/修改密码.svg";
import defaultAvatar from "../../../素材/svg/萌猫/奶牛猫.svg";

const AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024;
const PHONE_PATTERN = /^1[3-9]\d{9}$/;

const departments = ["生存保障部", "活动部", "宣传部", "秘书部", "养护部"] as const;

const userStore = useUserStore();
const isSubmitting = ref(false);
const avatarUrl = ref<string | null>(null);

const initialDepartment = normalizeInitialProfileText(userStore.currentUser?.department);

const form = reactive({
  nickname: normalizeInitialProfileText(userStore.currentUser?.nickname),
  department: departments.includes(initialDepartment as (typeof departments)[number]) ? initialDepartment : "",
  contact_info: normalizeInitialProfileText(userStore.currentUser?.contact_info),
});

const selectedDepartment = computed(() => form.department);
const departmentIndex = computed(() => {
  const index = departments.findIndex((department) => department === form.department);
  return index >= 0 ? index : 0;
});
const avatarLoadFailed = ref(false);
const avatarPreview = computed(() => avatarUrl.value || userStore.currentUser?.avatar_url || defaultAvatar);
const avatarDisplay = computed(() => (avatarLoadFailed.value ? defaultAvatar : avatarPreview.value));

watch(avatarPreview, () => {
  avatarLoadFailed.value = false;
});

function onDepartmentChange(event: any) {
  const index = Number(event.detail.value);
  form.department = departments[index] || departments[0];
}

function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const files = (result.tempFiles || []) as Array<{ size?: number }>;
      const fileSize = Number(files[0]?.size || 0);
      if (fileSize > AVATAR_MAX_SIZE_BYTES) {
        uni.showToast({ title: "头像图片不能超过 2MB", icon: "none" });
        return;
      }
      const tempPath = result.tempFilePaths[0];
      if (tempPath) {
        void uploadAvatar(tempPath);
      }
    },
  });
}

async function uploadAvatar(tempPath: string) {
  if (!userStore.accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  uni.showLoading({ title: "头像上传中", mask: true });
  try {
    const asset = await uploadUserAvatar(userStore.accessToken, tempPath, userStore.currentUser?.id);
    avatarUrl.value = asset.default_url;
    uni.hideLoading();
  } catch (error) {
    uni.hideLoading();
    const message = error instanceof Error ? error.message : "头像上传失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

function validateForm(): boolean {
  const nickname = form.nickname.trim();
  if (!nickname) {
    uni.showToast({ title: "请输入昵称", icon: "none" });
    return false;
  }

  if (Array.from(nickname).length > 20) {
    uni.showToast({ title: "昵称不能超过 20 个字符", icon: "none" });
    return false;
  }

  if (!form.department) {
    uni.showToast({ title: "请选择部门", icon: "none" });
    return false;
  }

  if (!PHONE_PATTERN.test(form.contact_info)) {
    uni.showToast({ title: "请输入正确的手机号", icon: "none" });
    return false;
  }

  form.nickname = nickname;
  return true;
}

async function submitProfile() {
  if (isSubmitting.value || !validateForm()) {
    return;
  }

  if (!userStore.accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isSubmitting.value = true;
  try {
    await userStore.completeCurrentProfile({
      nickname: form.nickname,
      avatar_url: avatarUrl.value,
      department: form.department,
      contact_info: form.contact_info,
    });
    uni.showToast({ title: "身份已初始化", icon: "success" });
    uni.reLaunch({ url: HOME_ROUTE });
  } catch (error) {
    const message = error instanceof Error ? error.message : "初始化失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.onboarding-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 10%, rgba(212, 235, 202, 0.9) 0, rgba(212, 235, 202, 0) 148rpx),
    linear-gradient(180deg, #fbfdf8 0%, #f5faef 100%);
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.background-cat {
  position: absolute;
  right: 24rpx;
  top: 132rpx;
  width: 220rpx;
  height: 254rpx;
  border-radius: 120rpx 120rpx 38rpx 38rpx;
  background: rgba(211, 230, 203, 0.3);
  opacity: 0.58;
}

.background-cat::before,
.background-cat::after {
  content: "";
  position: absolute;
  top: -26rpx;
  width: 72rpx;
  height: 72rpx;
  background: rgba(211, 230, 203, 0.7);
  transform: rotate(45deg);
}

.background-cat::before {
  left: 24rpx;
}

.background-cat::after {
  right: 24rpx;
}

.page-content {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  box-sizing: border-box;
  padding: 82rpx 36rpx 44rpx;
  display: flex;
  flex-direction: column;
  gap: 26rpx;
}

.hero {
  display: flex;
  align-items: center;
  gap: 28rpx;
  padding: 0 22rpx 18rpx;
}

.hero-icon {
  width: 126rpx;
  height: 126rpx;
  border-radius: 50%;
  background: rgba(207, 231, 197, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.hero-user {
  width: 78rpx;
  height: 78rpx;
  filter: brightness(0) saturate(100%) invert(34%) sepia(48%) saturate(897%) hue-rotate(80deg);
}

.hero-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.eyebrow-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.eyebrow-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: #2f8037;
}

.eyebrow {
  color: #2e7c35;
  font-size: 28rpx;
  font-weight: 800;
}

.hero-title {
  color: #1f2430;
  font-size: 62rpx;
  font-weight: 900;
  line-height: 1.08;
}

.hero-subtitle {
  color: #676d78;
  font-size: 25rpx;
  line-height: 1.45;
}

.form-card {
  border-radius: 42rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 28rpx 62rpx rgba(47, 100, 44, 0.12);
  padding: 42rpx 44rpx 34rpx;
}

.step-pill {
  width: 168rpx;
  height: 54rpx;
  margin: 0 auto 34rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #eef5eb 0%, #e0eddb 100%);
  color: #2e7c35;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 54rpx;
  text-align: center;
}

.field-group {
  margin-top: 30rpx;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 18rpx;
  color: #202124;
  font-size: 28rpx;
  font-weight: 900;
}

.required {
  color: #e85043;
}

.field-icon {
  width: 36rpx;
  height: 36rpx;
  filter: brightness(0) saturate(100%) invert(32%) sepia(50%) saturate(911%) hue-rotate(80deg);
}

.phone-icon {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: #2f8037;
  color: #ffffff;
  font-size: 22rpx;
  line-height: 36rpx;
  text-align: center;
}

.field-input,
.picker-field {
  width: 100%;
  height: 88rpx;
  box-sizing: border-box;
  border: 2rpx solid #dfe4e6;
  border-radius: 24rpx;
  background: #ffffff;
  color: #24272c;
  font-size: 27rpx;
}

.field-input {
  padding: 0 34rpx;
}

.input-placeholder,
.picker-placeholder {
  color: #9ca2ad;
}

.picker-field {
  padding: 0 30rpx 0 34rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-value {
  color: #24272c;
}

.picker-arrow {
  color: #737a84;
  font-size: 38rpx;
  line-height: 1;
}

.avatar-picker {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6rpx 0 0;
}

.avatar-shell {
  position: relative;
  width: 154rpx;
  height: 154rpx;
  border: 4rpx solid #eef2ec;
  border-radius: 50%;
  background: #f7fbf1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.avatar-image {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
}

.camera-badge {
  position: absolute;
  right: -4rpx;
  bottom: 4rpx;
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #2f8037;
  color: #ffffff;
  box-shadow: 0 8rpx 16rpx rgba(45, 132, 49, 0.22);
}

.camera-text {
  display: block;
  width: 48rpx;
  height: 48rpx;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 44rpx;
  text-align: center;
}

.avatar-copy {
  margin-top: 18rpx;
  color: #6f747b;
  font-size: 24rpx;
}

.avatar-rule {
  margin-top: 8rpx;
  color: #9097a0;
  font-size: 21rpx;
}

.privacy-note {
  min-height: 58rpx;
  margin-top: 16rpx;
  padding: 0 20rpx;
  border-radius: 18rpx;
  background: #f2f8ed;
  color: #617068;
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 22rpx;
}

.privacy-icon {
  width: 28rpx;
  height: 28rpx;
  filter: brightness(0) saturate(100%) invert(34%) sepia(48%) saturate(897%) hue-rotate(80deg);
  flex: 0 0 auto;
}

.primary-button {
  height: 90rpx;
  margin-top: 38rpx;
  border-radius: 28rpx;
  background: linear-gradient(90deg, #2e8a35 0%, #257c2a 100%);
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 900;
  line-height: 90rpx;
  box-shadow: 0 16rpx 28rpx rgba(45, 132, 49, 0.22);
}

.primary-button::after {
  border: 0;
}

.card-footnote {
  display: block;
  margin-top: 22rpx;
  color: #6f747b;
  font-size: 24rpx;
  text-align: center;
}
</style>
