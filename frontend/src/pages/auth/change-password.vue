<template>
  <view class="onboarding-page">
    <view class="background-cat" />
    <view class="page-content">
      <view class="hero">
        <view class="hero-icon">
          <image class="hero-shield" :src="shieldIcon" mode="aspectFit" />
          <image class="hero-paw" :src="pawIcon" mode="aspectFit" />
        </view>
        <view class="hero-copy">
          <view class="eyebrow-row">
            <view class="eyebrow-dot" />
            <text class="eyebrow">首次登录</text>
          </view>
          <text class="hero-title">修改密码</text>
          <text class="hero-subtitle">为了账号安全，请先修改初始密码后继续使用系统</text>
        </view>
      </view>

      <view class="form-card">
        <view class="step-pill">步骤 1 / 2</view>

        <view class="field-group">
          <view class="field-label">
            <image class="field-icon" :src="passwordIcon" mode="aspectFit" />
            <text>当前密码（初始密码）</text>
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

        <view class="divider" />

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
            <text>密码建议 8-20 位，包含字母与数字，可使用 @_!</text>
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
          确认修改并继续
        </button>
        <text class="card-footnote">修改后将进入身份初始化</text>
      </view>

      <view class="tip-card">
        <image class="tip-cat" :src="tipCat" mode="aspectFit" />
        <view class="tip-copy">
          <view class="tip-title-row">
            <text class="tip-title">温馨提示</text>
            <image class="tip-paw" :src="pawSoftIcon" mode="aspectFit" />
          </view>
          <text class="tip-line">这是您首次登录的必要设置步骤，</text>
          <text class="tip-line">完成后即可继续初始化校园猫协身份。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { HOME_ROUTE, LOGIN_ROUTE, PROFILE_SETUP_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import shieldIcon from "../../../素材/svg/登录页/修改密码.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪.svg";
import pawSoftIcon from "../../../素材/svg/登录页/猫爪1.svg";
import passwordIcon from "../../../素材/登录页素材/密码.svg";
import iconShow from "../../../素材/登录页素材/密码-显示.svg";
import iconHide from "../../../素材/登录页素材/密码-隐藏.svg";
import tipCat from "../../../素材/svg/萌猫/白猫.svg";

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

  if (!userStore.accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isSubmitting.value = true;
  try {
    const result = await userStore.changeCurrentPassword({ ...form });
    uni.showToast({ title: "密码已修改", icon: "success" });
    if (result.next_action === "complete_profile") {
      uni.redirectTo({ url: PROFILE_SETUP_ROUTE });
      return;
    }
    uni.reLaunch({ url: HOME_ROUTE });
  } catch (error) {
    const message = error instanceof Error ? error.message : "修改失败";
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
  right: 28rpx;
  top: 120rpx;
  width: 220rpx;
  height: 260rpx;
  border-radius: 120rpx 120rpx 36rpx 36rpx;
  background: rgba(211, 230, 203, 0.32);
  opacity: 0.55;
}

.background-cat::before,
.background-cat::after {
  content: "";
  position: absolute;
  top: -26rpx;
  width: 72rpx;
  height: 72rpx;
  background: rgba(211, 230, 203, 0.72);
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
  padding: 0 22rpx 20rpx;
}

.hero-icon {
  position: relative;
  width: 126rpx;
  height: 126rpx;
  border-radius: 50%;
  background: rgba(207, 231, 197, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.hero-shield {
  width: 74rpx;
  height: 74rpx;
  filter: brightness(0) saturate(100%) invert(33%) sepia(76%) saturate(593%) hue-rotate(79deg);
}

.hero-paw {
  position: absolute;
  width: 42rpx;
  height: 42rpx;
  filter: brightness(0) invert(1);
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
  gap: 16rpx;
  margin-bottom: 18rpx;
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
  padding: 0 34rpx;
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

.icon-button::after,
.primary-button::after {
  border: 0;
}

.eye-icon {
  width: 38rpx;
  height: 38rpx;
}

.divider {
  height: 2rpx;
  margin: 34rpx 0 0;
  background: #edf0f1;
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
  background: linear-gradient(90deg, #2e8a35 0%, #257c2a 100%);
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 900;
  line-height: 90rpx;
  box-shadow: 0 16rpx 28rpx rgba(45, 132, 49, 0.22);
}

.card-footnote {
  display: block;
  margin-top: 22rpx;
  color: #6f747b;
  font-size: 24rpx;
  text-align: center;
}

.tip-card {
  min-height: 148rpx;
  border: 2rpx solid rgba(202, 225, 195, 0.9);
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.74);
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 24rpx 28rpx;
}

.tip-cat {
  width: 128rpx;
  height: 128rpx;
  flex: 0 0 auto;
}

.tip-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tip-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.tip-title {
  color: #2f8037;
  font-size: 28rpx;
  font-weight: 900;
}

.tip-paw {
  width: 34rpx;
  height: 34rpx;
}

.tip-line {
  color: #5f666e;
  font-size: 24rpx;
  line-height: 1.42;
}
</style>
