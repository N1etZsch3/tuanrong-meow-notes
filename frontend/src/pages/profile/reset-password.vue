<template>
  <view class="password-page">
    <image class="page-bg" :src="pageBackground" mode="aspectFill" />
    <scroll-view class="password-scroll" scroll-y :show-scrollbar="false">
      <view class="password-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="nav-copy">
            <text class="nav-title">重设密码</text>
            <text class="nav-subtitle">请使用当前密码验证后设置新密码</text>
          </view>
        </view>

        <view class="form-card">
          <view class="field-group">
            <view class="field-label">
              <image class="field-icon" :src="passwordIcon" mode="aspectFit" />
              <text>当前密码</text>
            </view>
            <view class="input-row">
              <input
                v-model="form.old_password"
                class="field-input"
                :password="hidden.old"
                placeholder="请输入当前密码"
                placeholder-class="input-placeholder"
                maxlength="64"
              />
              <button class="icon-button" type="button" @tap="hidden.old = !hidden.old">
                <image class="eye-icon" :src="hidden.old ? iconHide : iconShow" mode="aspectFit" />
              </button>
            </view>
          </view>

          <view class="field-group">
            <view class="field-label">
              <image class="field-icon" :src="passwordIcon" mode="aspectFit" />
              <text>新密码</text>
            </view>
            <view class="input-row">
              <input
                v-model="form.new_password"
                class="field-input"
                :password="hidden.next"
                placeholder="请输入新密码"
                placeholder-class="input-placeholder"
                maxlength="20"
              />
              <button class="icon-button" type="button" @tap="hidden.next = !hidden.next">
                <image class="eye-icon" :src="hidden.next ? iconHide : iconShow" mode="aspectFit" />
              </button>
            </view>
            <view class="rule-box">
              <image class="rule-icon" :src="shieldIcon" mode="aspectFit" />
              <text>密码需 8-20 位，包含字母与数字，可使用 @_!</text>
            </view>
          </view>

          <view class="field-group">
            <view class="field-label">
              <image class="field-icon" :src="passwordIcon" mode="aspectFit" />
              <text>确认新密码</text>
            </view>
            <view class="input-row">
              <input
                v-model="form.confirm_password"
                class="field-input"
                :password="hidden.confirm"
                placeholder="请再次输入新密码"
                placeholder-class="input-placeholder"
                maxlength="20"
              />
              <button class="icon-button" type="button" @tap="hidden.confirm = !hidden.confirm">
                <image class="eye-icon" :src="hidden.confirm ? iconHide : iconShow" mode="aspectFit" />
              </button>
            </view>
          </view>

          <button class="primary-button" :loading="isSubmitting" @tap="submitPassword">
            提交重设密码
          </button>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import shieldIcon from "../../../素材/svg/登录页/修改密码.svg";
import passwordIcon from "../../../素材/登录页素材/密码.svg";
import iconShow from "../../../素材/登录页素材/密码-显示.svg";
import iconHide from "../../../素材/登录页素材/密码-隐藏.svg";
import pageBackground from "../../../素材/加载页素材/背景.jpg";

const userStore = useUserStore();
const isSubmitting = ref(false);

const form = reactive({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

const hidden = reactive({
  old: true,
  next: true,
  confirm: true,
});

function validatePassword(value: string): boolean {
  return (
    value.length >= 8 &&
    value.length <= 20 &&
    /^[A-Za-z0-9@_!]+$/.test(value) &&
    /[A-Za-z]/.test(value) &&
    /\d/.test(value)
  );
}

function validateForm(): boolean {
  if (!form.old_password) {
    uni.showToast({ title: "请输入当前密码", icon: "none" });
    return false;
  }

  if (!validatePassword(form.new_password)) {
    uni.showToast({ title: "新密码需为 8-20 位字母和数字组合", icon: "none" });
    return false;
  }

  if (form.new_password !== form.confirm_password) {
    uni.showToast({ title: "两次输入的新密码不一致", icon: "none" });
    return false;
  }

  if (form.old_password === form.new_password) {
    uni.showToast({ title: "新密码不能与当前密码相同", icon: "none" });
    return false;
  }

  return true;
}

async function submitPassword() {
  if (isSubmitting.value || !validateForm()) {
    return;
  }

  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isSubmitting.value = true;
  try {
    await userStore.changeCurrentPassword({ ...form });
    uni.showToast({ title: "密码已重设", icon: "success" });
    uni.navigateBack();
  } catch (error) {
    const message = error instanceof Error ? error.message : "重设失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}
</script>

<style scoped>
.password-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.password-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.password-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
  margin-bottom: 32rpx;
}

.back-button {
  width: 68rpx;
  height: 68rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #2f8037;
  font-size: 58rpx;
  line-height: 58rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.12);
}

.back-button::after,
.icon-button::after,
.primary-button::after {
  border: 0;
}

.nav-copy {
  min-width: 0;
}

.nav-title,
.nav-subtitle {
  display: block;
}

.nav-title {
  color: #171b22;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #656d78;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.form-card {
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18rpx 46rpx rgba(42, 63, 43, 0.1);
  padding: 34rpx;
}

.field-group + .field-group {
  margin-top: 30rpx;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 16rpx;
  color: #202124;
  font-size: 28rpx;
  font-weight: 900;
}

.field-icon {
  width: 36rpx;
  height: 36rpx;
  filter: brightness(0) saturate(100%) invert(32%) sepia(50%) saturate(911%) hue-rotate(80deg);
}

.input-row {
  height: 88rpx;
  border: 2rpx solid #dfe4e6;
  border-radius: 24rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
}

.field-input {
  min-width: 0;
  flex: 1;
  height: 88rpx;
  padding: 0 30rpx;
  box-sizing: border-box;
  color: #24272c;
  font-size: 27rpx;
}

.input-placeholder {
  color: #9ca2ad;
}

.icon-button {
  width: 84rpx;
  height: 84rpx;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye-icon {
  width: 38rpx;
  height: 38rpx;
}

.rule-box {
  min-height: 64rpx;
  margin-top: 16rpx;
  padding: 0 22rpx;
  border-radius: 18rpx;
  background: linear-gradient(90deg, rgba(236, 245, 231, 0.95), rgba(248, 251, 245, 0.95));
  color: #6a707a;
  display: flex;
  align-items: center;
  gap: 14rpx;
  font-size: 24rpx;
}

.rule-icon {
  width: 30rpx;
  height: 30rpx;
  filter: brightness(0) saturate(100%) invert(34%) sepia(48%) saturate(897%) hue-rotate(80deg);
  flex: 0 0 auto;
}

.primary-button {
  height: 90rpx;
  margin-top: 38rpx;
  border-radius: 28rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 90rpx;
}
</style>
