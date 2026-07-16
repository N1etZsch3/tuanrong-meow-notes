<template>
  <view class="login-page">
    <image class="page-bg" :src="loginBackground" mode="aspectFill" />

    <view class="content">
      <view class="hero">
        <view class="hero-icon" aria-label="成员登录图标">
          <image class="hero-person-img" :src="iconUser" mode="aspectFit" />
          <view class="hero-lock"><image class="hero-lock-img" :src="iconPassword" mode="aspectFit" /></view>
        </view>
        <view class="hero-copy">
          <text class="hero-title">成员登录</text>
          <text class="hero-subtitle">使用喵喵号登录校园猫协任务系统</text>
        </view>
      </view>

      <view class="login-card">
        <image class="association-logo" :src="logoImage" mode="aspectFit" />

        <view class="form-group">
          <view class="field-label">
            <image class="field-icon-img" :src="iconStudent" mode="aspectFit" />
            <text>喵喵号</text>
          </view>
          <input
            v-model.trim="form.meow_no"
            class="field-input"
            placeholder="请输入喵喵号"
            placeholder-class="input-placeholder"
            maxlength="64"
          />
        </view>

        <view class="form-group">
          <view class="field-label">
            <image class="field-icon-img" :src="iconPassword" mode="aspectFit" />
            <text>密码</text>
          </view>
          <view class="input-with-action">
            <input
              v-model="form.password"
              class="field-input inline-input"
              :password="passwordHidden"
              placeholder="请输入密码"
              placeholder-class="input-placeholder"
              maxlength="64"
            />
            <button class="icon-action" type="button" @tap="togglePassword">
              <image class="action-icon-img" :src="passwordHidden ? iconHide : iconShow" mode="aspectFit" />
            </button>
          </view>
        </view>

        <view class="form-group">
          <view class="field-label">
            <image class="field-icon-img" :src="iconCaptcha" mode="aspectFit" />
            <text>字母验证码</text>
          </view>
          <view class="captcha-row">
            <input
              v-model.trim="form.captcha_code"
              class="field-input captcha-input"
              placeholder="请输入验证码"
              placeholder-class="input-placeholder"
              maxlength="8"
            />
            <view class="captcha-panel" @tap="loadCaptcha">
              <image
                v-if="captchaImage"
                class="captcha-image"
                :src="captchaImage"
                mode="aspectFit"
              />
              <text v-else class="captcha-placeholder">验证码占位</text>
            </view>
          </view>
          <button class="refresh-captcha" type="button" @tap="loadCaptcha">
            看不清？换一张
          </button>
        </view>

        <button class="login-button" :loading="isLoading" @tap="handleLogin">
          登录
        </button>

        <view class="help-line">
          <text class="help-icon">?</text>
          <text>如无法登录，请联系管理员</text>
        </view>

        <view class="guest-entry" @tap="goPublicHome">
          <text class="guest-entry-text">先随便逛逛</text>
          <text class="guest-entry-arrow">→</text>
        </view>
      </view>

      <view class="agreement">
        <checkbox-group @change="onAgreementChange">
          <label class="checkbox-label">
            <checkbox
              value="agreed"
              :checked="form.agreed"
              color="#33823b"
              style="transform: scale(0.7)"
            />
            <view class="agreement-text">
              <text>我已阅读并同意</text>
              <text class="agreement-link" @tap.stop="openPrivacyContract">
                《团绒喵记本小程序隐私保护指引》
              </text>
            </view>
          </label>
        </checkbox-group>
      </view>

      <view class="notice-card">
        <image class="notice-cat" :src="loginCat" mode="aspectFit" />
        <view class="notice-copy">
          <text>本系统仅限校园猫协成员使用，</text>
          <text>请使用喵喵号登录并严格遵守任务与救助规范，</text>
          <text>共同守护校园猫咪安全与健康。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import { getCaptcha, type LoginResponse } from "@/api/auth";
import { CHANGE_PASSWORD_ROUTE, HOME_ROUTE, PROFILE_SETUP_ROUTE, PUBLIC_HOME_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { requestWechatLoginCode } from "@/services/wechat-auth";
import { useUserStore } from "@/stores/user";
import {
  hasAcceptedAgreementForAccount,
  rememberAgreementAcceptedForAccounts,
} from "@/pages/login/agreement";

import loginBackground from "../../../素材/加载页素材/背景.jpg";
import loginCat from "../../../素材/svg/萌猫/三花猫.svg";
import logoImage from "../../../素材/登录页素材/协会徽标.jpg";
import iconStudent from "../../../素材/登录页素材/学号.svg";
import iconPassword from "../../../素材/登录页素材/密码.svg";
import iconCaptcha from "../../../素材/登录页素材/验证码.svg";
import iconUser from "../../../素材/登录页素材/登录.svg";
import iconShow from "../../../素材/登录页素材/密码-显示.svg";
import iconHide from "../../../素材/登录页素材/密码-隐藏.svg";

declare const wx: {
  openPrivacyContract(options: { fail?: () => void }): void;
};

const userStore = useUserStore();

const form = reactive({
  meow_no: "",
  password: "",
  captcha_code: "",
  captcha_id: "",
  agreed: false,
});

const passwordHidden = ref(true);
const captchaImage = ref("");
const isLoading = ref(false);
const isConfirmingBinding = ref(false);
const WECHAT_BINDING_CONFIRMATION_REQUIRED = 40006;

function goPublicHome() {
  uni.reLaunch({ url: PUBLIC_HOME_ROUTE });
}

function onAgreementChange(e: any) {
  form.agreed = e.detail.value.length > 0;
}

function openPrivacyContract() {
  // #ifdef MP-WEIXIN
  wx.openPrivacyContract({
    fail: () => {
      uni.showToast({ title: "隐私保护指引暂时无法打开", icon: "none" });
    },
  });
  // #endif

  // #ifndef MP-WEIXIN
  uni.showToast({ title: "请在微信小程序中查看隐私保护指引", icon: "none" });
  // #endif
}

function applyRememberedAgreement() {
  form.agreed = hasAcceptedAgreementForAccount(form.meow_no);
}

function togglePassword() {
  passwordHidden.value = !passwordHidden.value;
}

async function loadCaptcha() {
  try {
    const captcha = await getCaptcha();
    form.captcha_id = captcha.captcha_id;
    captchaImage.value = captcha.captcha_image;
  } catch {
    form.captcha_id = "";
    captchaImage.value = "";
  }
}

function validateForm(): boolean {
  if (!form.meow_no) {
    uni.showToast({ title: "请输入喵喵号", icon: "none" });
    return false;
  }

  if (!form.password) {
    uni.showToast({ title: "请输入密码", icon: "none" });
    return false;
  }

  if (!form.captcha_id || !form.captcha_code) {
    uni.showToast({ title: "请输入验证码", icon: "none" });
    return false;
  }

  return true;
}

function confirmWechatBindingLogin(): Promise<boolean> {
  return new Promise((resolve) => {
    uni.showModal({
      title: "微信账号绑定",
      content: "登录后，当前微信将自动与该喵喵号绑定，用于后续自动登录和账号保护。如需更换微信，请联系管理员解绑。",
      confirmText: "确认登录",
      cancelText: "取消",
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false),
    });
  });
}

async function attemptPasswordLogin(bindWechat: boolean): Promise<LoginResponse | null> {
  const wechatCode = await requestWechatLoginCode();
  if (!wechatCode) {
    uni.showToast({ title: "暂时无法获取微信登录凭证，请重试", icon: "none" });
    return null;
  }

  return userStore.loginWithPassword({
    meow_no: form.meow_no,
    password: form.password,
    captcha_id: form.captcha_id,
    captcha_code: form.captcha_code,
    agree_terms: form.agreed,
    wechat_code: wechatCode,
    agree_wechat_bind: bindWechat,
  });
}

function completePasswordLogin(result: LoginResponse) {
  rememberAgreementAcceptedForAccounts([
    form.meow_no,
    result.user.meow_no,
    result.user.student_no,
  ]);

  if (result.next_action === "change_password" || result.must_change_password) {
    uni.showToast({ title: "请先修改初始密码", icon: "none" });
    uni.redirectTo({ url: CHANGE_PASSWORD_ROUTE });
    return;
  }

  if (result.next_action === "complete_profile") {
    uni.redirectTo({ url: PROFILE_SETUP_ROUTE });
    return;
  }

  uni.reLaunch({ url: HOME_ROUTE });
}

async function handleLoginFailure(error: unknown) {
  const message = error instanceof Error ? error.message : "登录失败";
  uni.showToast({ title: message, icon: "none" });
  await loadCaptcha();
}

async function handleLogin() {
  if (isLoading.value || isConfirmingBinding.value || !validateForm()) {
    return;
  }

  isLoading.value = true;
  try {
    let result: LoginResponse | null;
    try {
      result = await attemptPasswordLogin(false);
    } catch (error) {
      if (
        !(error instanceof ApiBusinessError && error.code === WECHAT_BINDING_CONFIRMATION_REQUIRED)
      ) {
        await handleLoginFailure(error);
        return;
      }

      isLoading.value = false;
      isConfirmingBinding.value = true;
      const confirmed = await confirmWechatBindingLogin();
      isConfirmingBinding.value = false;
      if (!confirmed) {
        return;
      }

      isLoading.value = true;
      try {
        result = await attemptPasswordLogin(true);
      } catch (retryError) {
        await handleLoginFailure(retryError);
        return;
      }
    }

    if (result) {
      completePasswordLogin(result);
    }
  } finally {
    isLoading.value = false;
    isConfirmingBinding.value = false;
  }
}

onMounted(() => {
  applyRememberedAgreement();
  void loadCaptcha();
});

watch(
  () => form.meow_no,
  () => {
    applyRememberedAgreement();
  },
);
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #f5faf0;
  font-family: "Songti SC", "STSong", "SimSun", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.content {
  position: relative;
  z-index: 1;
  height: 100vh;
  overflow: hidden;
  box-sizing: border-box;
  padding: 110rpx 36rpx 80rpx;
  display: flex;
  flex-direction: column;
}

.hero {
  display: flex;
  align-items: center;
  gap: 28rpx;
  padding: 0 36rpx 60rpx;
  flex: 0 0 auto;
}

.hero-icon {
  position: relative;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(196, 227, 184, 0.78);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #26742b;
}

.hero-person-img {
  width: 68rpx;
  height: 68rpx;
}

.hero-lock {
  position: absolute;
  right: 6rpx;
  bottom: 6rpx;
  width: 38rpx;
  height: 38rpx;
  border-radius: 50%;
  background: #2d7a32;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-lock-img {
  width: 22rpx;
  height: 22rpx;
  filter: brightness(0) invert(1);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.hero-title {
  color: #1f7228;
  font-size: 56rpx;
  font-weight: 900;
  letter-spacing: 6rpx;
  line-height: 1.1;
}

.hero-subtitle {
  color: #5e636c;
  font-size: 26rpx;
  font-weight: 500;
}

.login-card {
  border-radius: 42rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 28rpx 62rpx rgba(47, 100, 44, 0.12);
  padding: 34rpx 44rpx 36rpx;
  flex: 0 0 auto;
}

.association-logo {
  width: 140rpx;
  height: 140rpx;
  margin: 0 auto 28rpx;
  display: block;
}

.form-group {
  margin-top: 24rpx;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 16rpx;
  color: #202124;
  font-size: 28rpx;
  font-weight: 800;
  margin: 0 8rpx 12rpx;
}

.field-icon-img {
  width: 36rpx;
  height: 36rpx;
}

.field-input,
.input-with-action {
  height: 84rpx;
  box-sizing: border-box;
  border: 2rpx solid #e0e4e5;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 18rpx rgba(42, 64, 44, 0.04);
}

.field-input {
  width: 100%;
  padding: 0 34rpx;
  color: #24272c;
  font-size: 26rpx;
}

.input-placeholder {
  color: #9da3ad;
}

.input-with-action {
  display: flex;
  align-items: center;
  overflow: hidden;
}

.inline-input {
  flex: 1;
  width: 0;
  height: 100%;
  border: 0;
  box-shadow: none;
  background: transparent;
}

.icon-action {
  width: 84rpx;
  height: 84rpx;
  margin: 0 4rpx 0 0;
  padding: 0;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon-img {
  width: 40rpx;
  height: 40rpx;
}

.icon-action::after,
.refresh-captcha::after,
.login-button::after {
  border: 0;
}

.captcha-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 196rpx;
  gap: 16rpx;
  align-items: center;
}

.captcha-input {
  min-width: 0;
}

.captcha-panel {
  height: 84rpx;
  border: 2rpx solid #d8e8cf;
  border-radius: 22rpx;
  background: #fbfff7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.captcha-image {
  width: 100%;
  height: 100%;
}

.captcha-placeholder {
  color: #2f7b2e;
  font-size: 22rpx;
  font-weight: 700;
}

.refresh-captcha {
  display: block;
  margin: 16rpx 0 0 auto;
  padding: 0;
  background: transparent;
  color: #6f747b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.login-button {
  height: 88rpx;
  margin-top: 36rpx;
  border-radius: 28rpx;
  background: linear-gradient(90deg, #2e8a35 0%, #257c2a 100%);
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 88rpx;
  box-shadow: 0 12rpx 28rpx rgba(45, 132, 49, 0.2);
}

.help-line {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: #6f747b;
  font-size: 22rpx;
}

.help-icon {
  width: 30rpx;
  height: 30rpx;
  border: 2rpx solid #8d9299;
  border-radius: 50%;
  line-height: 28rpx;
  text-align: center;
  font-size: 22rpx;
}

.guest-entry {
  margin-top: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.guest-entry-text {
  color: #33823b;
  font-size: 26rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.guest-entry-arrow {
  color: #33823b;
  font-size: 26rpx;
  font-weight: 700;
}

.agreement {
  margin: 28rpx 22rpx 0;
  flex: 0 0 auto;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.agreement-text {
  flex: 1;
  color: #5f666e;
  font-size: 21rpx;
  line-height: 1.55;
}

.agreement-link {
  color: #297a2f;
}

.notice-card {
  margin-top: auto;
  min-height: 140rpx;
  border: 2rpx solid rgba(202, 225, 195, 0.9);
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 24rpx 30rpx;
}

.notice-cat {
  width: 110rpx;
  height: 110rpx;
  flex: 0 0 auto;
}

.notice-copy {
  display: flex;
  flex-direction: column;
  gap: 9rpx;
  color: #5f666e;
  font-size: 24rpx;
  line-height: 1.36;
}
</style>
