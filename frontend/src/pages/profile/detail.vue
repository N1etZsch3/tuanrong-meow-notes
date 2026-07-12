<template>
  <view class="detail-page">
    <scroll-view class="detail-scroll" scroll-y>
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <text class="nav-title">个人资料</text>
        </view>

        <view class="avatar-panel">
          <view class="avatar-shell" @tap="chooseAvatar">
            <image
              class="avatar"
              :src="avatarDisplay"
              mode="aspectFill"
              @error="avatarLoadFailed = true"
            />
            <text class="avatar-plus">+</text>
          </view>
          <text class="avatar-note">点击更换头像，图片不超过 2MB</text>
          <text v-if="avatarReviewHint" class="avatar-review-hint">{{ avatarReviewHint }}</text>
        </view>

        <view class="form-card">
          <view class="field-group">
            <text class="field-label">昵称</text>
            <input v-model="form.nickname" class="field-input" maxlength="20" placeholder="请输入昵称" />
          </view>

          <view class="field-group">
            <text class="field-label">部门</text>
            <picker mode="selector" :range="departments" :value="departmentIndex" @change="onDepartmentChange">
              <view class="picker-field">
                <text :class="form.department ? 'picker-value' : 'picker-placeholder'">
                  {{ form.department || "请选择部门" }}
                </text>
                <text class="picker-arrow">⌄</text>
              </view>
            </picker>
          </view>

          <view class="field-group">
            <text class="field-label">联系方式</text>
            <input
              v-model.trim="form.contact_info"
              class="field-input"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
            />
            <text class="privacy-note">手机号仅管理员可见，用于任务协作时必要联系。</text>
          </view>

          <view class="field-group">
            <text class="field-label">喵喵号</text>
            <view class="readonly-field">{{ profile?.meow_no || userStore.currentUser?.meow_no || "--" }}</view>
          </view>

          <view class="field-group">
            <text class="field-label">身份</text>
            <view class="readonly-field">{{ roleLabel }}</view>
          </view>
        </view>

        <button class="save-button" :loading="isSaving" @tap="saveProfile">保存资料</button>
      </view>
    </scroll-view>
    <!-- #ifdef MP-WEIXIN -->
    <page-container
      :show="pageLeaveGuardArmed"
      :overlay="false"
      :duration="0"
      @beforeleave="handleNativePageLeave"
    />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import { onShow } from "@dcloudio/uni-app";

import { resolveUserAvatarContentUrl, uploadUserAvatar } from "@/api/files";
import { getMyProfile, updateMyProfile, type MyProfileResponse } from "@/api/profile";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import { createPageLeaveGuard } from "@/utils/page-leave-guard";

import {
  createProfileEditSnapshot,
  hasUnsavedProfileChanges,
  type ProfileEditSnapshot,
} from "./profile-edit-guard";
import { getRoleLabel } from "./profile-page";
import defaultAvatar from "../../../素材/svg/萌猫/橘猫.svg";

const AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024;
const PHONE_PATTERN = /^1[3-9]\d{9}$/;
const departments = ["生存保障部", "活动部", "宣传部", "秘书部", "养护部"] as const;

const userStore = useUserStore();
const profile = ref<MyProfileResponse | null>(null);
const avatarUrl = ref<string | null>(null);
const avatarReviewStatus = ref<"idle" | "pending" | "passed" | "rejected" | "failed">("idle");
const isSaving = ref(false);
const savedProfileSnapshot = ref<ProfileEditSnapshot | null>(null);
const nativePageLeaveGuardReady = ref(true);
const isNavigatingAway = ref(false);

const form = reactive({
  nickname: "",
  department: "",
  contact_info: "",
});

const avatarLoadFailed = ref(false);
const avatarPreview = computed(() => avatarUrl.value || profile.value?.avatar_url || defaultAvatar);
const avatarDisplay = computed(() => (avatarLoadFailed.value ? defaultAvatar : avatarPreview.value));
const avatarReviewHint = computed(() => {
  if (avatarReviewStatus.value === "pending") {
    return "图片已上传，审核通过后自动生效";
  }
  if (["rejected", "failed"].includes(avatarReviewStatus.value)) {
    return "头像审核未通过，请更换图片后重试";
  }
  return "";
});

watch(avatarPreview, () => {
  avatarLoadFailed.value = false;
});
const roleLabel = computed(() => getRoleLabel(profile.value?.role || userStore.currentUser?.role));
const departmentIndex = computed(() => {
  const index = departments.findIndex((department) => department === form.department);
  return index >= 0 ? index : 0;
});
const pageLeaveGuard = createPageLeaveGuard(
  () => !isSaving.value && hasPendingProfileChanges(),
);
const pageLeaveGuardArmed = computed(
  () =>
    nativePageLeaveGuardReady.value &&
    !isNavigatingAway.value &&
    !isSaving.value &&
    hasPendingProfileChanges(),
);

function applyProfile(nextProfile: MyProfileResponse) {
  profile.value = nextProfile;
  avatarUrl.value = resolveUserAvatarContentUrl(nextProfile.avatar_url);
  avatarReviewStatus.value = nextProfile.avatar_review_status;
  form.nickname = nextProfile.nickname;
  form.department = nextProfile.department || "";
  form.contact_info = nextProfile.contact_info || "";
  savedProfileSnapshot.value = createProfileEditSnapshot({
    nickname: form.nickname,
    department: form.department,
    contact_info: form.contact_info,
    avatar_url: avatarUrl.value,
  });
  pageLeaveGuard.reset();
}

async function loadProfile() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  try {
    applyProfile(await getMyProfile(accessToken));
  } catch (error) {
    const message = error instanceof Error ? error.message : "资料加载失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

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
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  uni.showLoading({ title: "头像上传中", mask: true });
  try {
    const asset = await uploadUserAvatar(accessToken, tempPath, userStore.currentUser?.id);
    avatarUrl.value = tempPath;
    avatarReviewStatus.value = asset.security_status === "pending" ? "pending" : "passed";
    if (savedProfileSnapshot.value) {
      savedProfileSnapshot.value = { ...savedProfileSnapshot.value, avatar_url: tempPath };
    }
    uni.hideLoading();
    uni.showToast({ title: asset.review_message || "头像已提交", icon: "none" });
  } catch (error) {
    uni.hideLoading();
    const message = error instanceof Error ? error.message : "头像上传失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

function validateProfile(): boolean {
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

async function saveProfile() {
  if (isSaving.value || !validateProfile()) {
    return;
  }
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isSaving.value = true;
  try {
    const updatedProfile = await updateMyProfile(
      {
        nickname: form.nickname,
        department: form.department,
        contact_info: form.contact_info,
      },
      accessToken,
    );
    applyProfile(updatedProfile);
    if (userStore.currentUser) {
      userStore.setCurrentUser({
        ...userStore.currentUser,
        nickname: updatedProfile.nickname,
        avatar_url: updatedProfile.avatar_url,
        department: updatedProfile.department,
        contact_info: updatedProfile.contact_info,
      });
    }
    uni.showToast({ title: "资料已保存", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSaving.value = false;
  }
}

function goBack() {
  if (!hasPendingProfileChanges()) {
    isNavigatingAway.value = true;
    uni.navigateBack();
    return;
  }
  requestPageLeave();
}

function requestPageLeave() {
  const request = pageLeaveGuard.requestLeave();
  if (request === "leave") {
    releasePageLeaveGuardAndNavigateBack();
    return;
  }
  if (request === "confirm") {
    confirmDiscardProfileChanges();
  }
}

function handleNativePageLeave() {
  if (isNavigatingAway.value) {
    return;
  }
  nativePageLeaveGuardReady.value = false;
  requestPageLeave();
}

function releasePageLeaveGuardAndNavigateBack() {
  if (isNavigatingAway.value) {
    return;
  }
  isNavigatingAway.value = true;
  nativePageLeaveGuardReady.value = false;
  nextTick(() => {
    uni.navigateBack();
  });
}

function rearmNativePageLeaveGuard() {
  isNavigatingAway.value = false;
  nativePageLeaveGuardReady.value = false;
  nextTick(() => {
    nativePageLeaveGuardReady.value = true;
  });
}

function hasPendingProfileChanges() {
  return hasUnsavedProfileChanges(savedProfileSnapshot.value, {
    nickname: form.nickname,
    department: form.department,
    contact_info: form.contact_info,
    avatar_url: avatarUrl.value,
  });
}

function confirmDiscardProfileChanges() {
  uni.showModal({
    title: "放弃修改",
    content: "修改尚未保存，是否放弃？",
    confirmText: "放弃",
    confirmColor: "#d73546",
    cancelText: "继续编辑",
    success: (result) => {
      if (result.confirm && pageLeaveGuard.confirmDiscard()) {
        releasePageLeaveGuardAndNavigateBack();
        return;
      }
      pageLeaveGuard.cancelDiscard();
      rearmNativePageLeaveGuard();
    },
  });
}

onShow(() => {
  void loadProfile();
});
</script>

<style scoped>
.detail-page {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfcfb 0%, #f5faef 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.detail-scroll {
  height: 100vh;
}

.detail-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #ffffff;
  color: #2f8037;
  font-size: 58rpx;
  line-height: 54rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.1);
}

.back-button::after,
.save-button::after {
  border: 0;
}

.nav-title {
  color: #171b22;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.avatar-panel {
  margin: 42rpx 0 26rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-shell {
  position: relative;
}

.avatar {
  width: 164rpx;
  height: 164rpx;
  border: 8rpx solid #ffffff;
  border-radius: 50%;
  background: #edf6e9;
  box-shadow: 0 18rpx 38rpx rgba(42, 63, 43, 0.14);
}

.avatar-plus {
  position: absolute;
  right: 0;
  bottom: 10rpx;
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background: #2f8037;
  color: #ffffff;
  font-size: 36rpx;
  line-height: 46rpx;
  text-align: center;
}

.avatar-note {
  margin-top: 18rpx;
  color: #737b84;
  font-size: 24rpx;
}

.avatar-review-hint {
  color: #9a6826;
  font-size: 24rpx;
  line-height: 1.5;
  text-align: center;
}

.form-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
  padding: 30rpx;
}

.field-group + .field-group {
  margin-top: 28rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: #20242a;
  font-size: 27rpx;
  font-weight: 900;
}

.field-input,
.picker-field,
.readonly-field {
  box-sizing: border-box;
  width: 100%;
  min-height: 82rpx;
  border: 2rpx solid #dfe5e1;
  border-radius: 22rpx;
  background: #ffffff;
  color: #23272e;
  font-size: 27rpx;
  padding: 0 28rpx;
}

.picker-field,
.readonly-field {
  display: flex;
  align-items: center;
}

.picker-field {
  justify-content: space-between;
}

.picker-placeholder {
  color: #98a0a8;
}

.picker-arrow {
  color: #717982;
  font-size: 34rpx;
}

.privacy-note {
  display: block;
  margin-top: 12rpx;
  color: #758078;
  font-size: 22rpx;
}

.save-button {
  height: 88rpx;
  margin-top: 34rpx;
  border-radius: 28rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 88rpx;
}
</style>
