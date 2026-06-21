<template>
  <view class="login-page">
    <image class="page-bg" :src="loginBackground" mode="aspectFill" />

    <view class="content">
      <view class="hero">
        <view class="hero-icon" aria-label="成员登录图标">
          <text class="hero-person">员</text>
          <text class="hero-lock">锁</text>
        </view>
        <view class="hero-copy">
          <text class="hero-title">成员登录</text>
          <text class="hero-subtitle">使用学号登录校园猫协任务系统</text>
        </view>
      </view>

      <view class="login-card">
        <view class="association-logo placeholder">
          <text class="logo-main">校园猫协</text>
          <text class="logo-sub">Cat Fanciers Association</text>
          <text class="placeholder-label">徽标占位</text>
        </view>

        <view class="form-group">
          <view class="field-label">
            <text class="field-icon">学</text>
            <text>学号</text>
          </view>
          <input
            v-model.trim="form.student_no"
            class="field-input"
            placeholder="请输入学号"
            placeholder-class="input-placeholder"
            maxlength="64"
          />
        </view>

        <view class="form-group">
          <view class="field-label">
            <text class="field-icon">密</text>
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
            <button class="text-action" type="button" @tap="togglePassword">
              {{ passwordHidden ? "显示" : "隐藏" }}
            </button>
          </view>
        </view>

        <view class="form-group">
          <view class="field-label">
            <text class="field-icon">验</text>
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

        <button class="login-button" :loading="submitting" @tap="handleLogin">
          登录
        </button>

        <view class="help-line">
          <text class="help-icon">?</text>
          <text>如无法登录，请联系管理员</text>
        </view>
      </view>

      <view class="agreement-row" @tap="toggleAgreement">
        <view class="checkbox" :class="{ checked: form.agree_terms }">
          <text v-if="form.agree_terms">✓</text>
        </view>
        <text class="agreement-text">
          我已阅读并同意
          <text class="agreement-link">《用户协议》</text>
          <text class="agreement-link">《隐私政策》</text>
          <text class="agreement-link">《校园猫协成员规范》</text>
        </text>
      </view>

      <view class="notice-card">
        <image class="notice-cat" :src="loginCat" mode="aspectFit" />
        <view class="notice-copy">
          <text>本系统仅限校园猫协成员使用，</text>
          <text>请使用学号登录并严格遵守任务与救助规范，</text>
          <text>共同守护校园猫咪安全与健康。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { getCaptcha } from "@/api/auth";
import { useUserStore } from "@/stores/user";

import loginBackground from "../../../素材/登录页背景.png";
import loginCat from "../../../素材/登陆页猫猫头.png";

const userStore = useUserStore();

const form = reactive({
  student_no: "",
  password: "",
  captcha_id: "",
  captcha_code: "",
  agree_terms: false,
});

const captchaImage = ref("");
const passwordHidden = ref(true);
const submitting = ref(false);

function togglePassword() {
  passwordHidden.value = !passwordHidden.value;
}

function toggleAgreement() {
  form.agree_terms = !form.agree_terms;
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
  if (!form.student_no) {
    uni.showToast({ title: "请输入学号", icon: "none" });
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

  if (!form.agree_terms) {
    uni.showToast({ title: "请先勾选协议", icon: "none" });
    return false;
  }

  return true;
}

async function handleLogin() {
  if (submitting.value || !validateForm()) {
    return;
  }

  submitting.value = true;
  try {
    const result = await userStore.loginWithPassword({ ...form });
    if (result.must_change_password) {
      uni.showToast({ title: "请先修改初始密码", icon: "none" });
      return;
    }

    uni.reLaunch({ url: "/pages/index/index" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "登录失败";
    uni.showToast({ title: message, icon: "none" });
    await loadCaptcha();
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  void loadCaptcha();
});
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #f5faf0;
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
  min-height: 100vh;
  box-sizing: border-box;
  padding: 108rpx 36rpx 56rpx;
}

.hero {
  display: flex;
  align-items: center;
  gap: 28rpx;
  padding: 0 36rpx 76rpx;
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
  font-size: 50rpx;
  font-weight: 800;
}

.hero-person {
  transform: translateY(-2rpx);
}

.hero-lock {
  position: absolute;
  right: 10rpx;
  bottom: 8rpx;
  width: 44rpx;
  height: 36rpx;
  border-radius: 10rpx;
  background: #2d7a32;
  color: #ffffff;
  font-size: 18rpx;
  line-height: 36rpx;
  text-align: center;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.hero-title {
  color: #1f7228;
  font-size: 62rpx;
  font-weight: 900;
  letter-spacing: 6rpx;
  line-height: 1.1;
}

.hero-subtitle {
  color: #5e636c;
  font-size: 28rpx;
  font-weight: 500;
}

.login-card {
  border-radius: 42rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 28rpx 62rpx rgba(47, 100, 44, 0.12);
  padding: 42rpx 44rpx 44rpx;
}

.association-logo {
  width: 188rpx;
  height: 188rpx;
  margin: 0 auto 46rpx;
  border: 5rpx solid #1c1c1c;
  border-radius: 28rpx;
  transform: rotate(-1deg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #1f1f1f;
  background: #ffffff;
}

.placeholder {
  position: relative;
}

.logo-main {
  font-size: 30rpx;
  font-weight: 800;
}

.logo-sub {
  margin-top: 8rpx;
  font-size: 20rpx;
  font-weight: 700;
  text-align: center;
  line-height: 1.15;
}

.placeholder-label {
  position: absolute;
  bottom: -26rpx;
  color: #9b9b9b;
  font-size: 18rpx;
}

.form-group {
  margin-top: 34rpx;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 16rpx;
  color: #202124;
  font-size: 30rpx;
  font-weight: 800;
  margin: 0 8rpx 16rpx;
}

.field-icon {
  width: 36rpx;
  height: 36rpx;
  border-radius: 10rpx;
  background: #33823b;
  color: #ffffff;
  font-size: 22rpx;
  line-height: 36rpx;
  text-align: center;
}

.field-input,
.input-with-action {
  height: 92rpx;
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
  font-size: 28rpx;
}

.input-placeholder {
  color: #9da3ad;
}

.input-with-action {
  display: flex;
  align-items: center;
}

.inline-input {
  flex: 1;
  border: 0;
  box-shadow: none;
}

.text-action {
  min-width: 104rpx;
  margin: 0 18rpx 0 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: #8a9099;
  font-size: 24rpx;
  line-height: 92rpx;
}

.text-action::after,
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
  height: 92rpx;
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
  font-size: 24rpx;
  font-weight: 700;
}

.refresh-captcha {
  display: block;
  margin: 16rpx 0 0 auto;
  padding: 0;
  background: transparent;
  color: #6f747b;
  font-size: 24rpx;
  line-height: 32rpx;
}

.login-button {
  height: 88rpx;
  margin-top: 46rpx;
  border-radius: 28rpx;
  background: linear-gradient(90deg, #2e8a35 0%, #257c2a 100%);
  color: #ffffff;
  font-size: 34rpx;
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
  font-size: 24rpx;
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

.agreement-row {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  margin: 34rpx 22rpx 0;
}

.checkbox {
  width: 32rpx;
  height: 32rpx;
  flex: 0 0 auto;
  border: 2rpx solid #a9afb7;
  border-radius: 8rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #ffffff;
  font-size: 24rpx;
  line-height: 32rpx;
  text-align: center;
}

.checkbox.checked {
  border-color: #2f8337;
  background: #2f8337;
}

.agreement-text {
  flex: 1;
  color: #5f666e;
  font-size: 25rpx;
  line-height: 1.55;
}

.agreement-link {
  color: #297a2f;
}

.notice-card {
  margin-top: 36rpx;
  min-height: 156rpx;
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
  font-size: 26rpx;
  line-height: 1.36;
}
</style>
