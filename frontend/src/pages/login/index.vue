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
              <text class="agreement-link" @tap.stop="openModal('用户协议')">《用户协议》</text>
              <text class="agreement-link" @tap.stop="openModal('隐私政策')">《隐私政策》</text>
              <text class="agreement-link" @tap.stop="openModal('校园猫协成员规范')">《校园猫协成员规范》</text>
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

    <view v-if="showModal" class="modal-mask" @tap="closeModal">
      <view class="modal-card" @tap.stop>
        <image class="modal-corner-paw modal-corner-paw-left" :src="pawIcon" mode="aspectFit" />
        <image class="modal-corner-paw modal-corner-paw-right" :src="pawSoftIcon" mode="aspectFit" />
        <button class="modal-close" type="button" aria-label="关闭弹窗" @tap="closeModal">×</button>
        <view class="modal-header">
          <image class="paw-icon left-paw" :src="pawSoftIcon" mode="aspectFit" />
          <text class="modal-title">{{ modalTitle }}</text>
          <image class="paw-icon right-paw" :src="pawLineIcon" mode="aspectFit" />
        </view>

        <view class="modal-body">
          <view class="modal-joke-card">
            <image class="modal-cat" :src="modalCat" mode="aspectFit" />
            <text class="modal-joke-title">骗你的，其实什么也没有。</text>
            <view class="modal-joke-mark">
              <view class="modal-joke-dot" />
              <view class="modal-joke-leaf" />
              <view class="modal-joke-dot" />
            </view>
            <text class="modal-joke-sub">♥ 喵~ 你也太可爱了吧！♥</text>
          </view>
        </view>

        <button class="modal-btn" hover-class="modal-btn-hover" @tap="closeModal">
          <image class="btn-paw-icon" :src="pawSoftIcon" mode="aspectFit" />
          <text>知道啦</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { getCaptcha } from "@/api/auth";
import { CHANGE_PASSWORD_ROUTE, HOME_ROUTE, PROFILE_SETUP_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import loginBackground from "../../../素材/登录页素材/登录页背景.png";
import loginCat from "../../../素材/svg/萌猫/三花猫.svg";
import logoImage from "../../../素材/登录页素材/协会徽标.jpg";
import iconStudent from "../../../素材/登录页素材/学号.svg";
import iconPassword from "../../../素材/登录页素材/密码.svg";
import iconCaptcha from "../../../素材/登录页素材/验证码.svg";
import iconUser from "../../../素材/登录页素材/登录.svg";
import iconShow from "../../../素材/登录页素材/密码-显示.svg";
import iconHide from "../../../素材/登录页素材/密码-隐藏.svg";
import modalCat from "../../../素材/svg/萌猫/橘猫.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪.svg";
import pawSoftIcon from "../../../素材/svg/登录页/猫爪1.svg";
import pawLineIcon from "../../../素材/svg/登录页/猫爪-copy-copy.svg";

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
const showModal = ref(false);
const modalTitle = ref("");

const openModal = (title: string) => {
  modalTitle.value = title;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

function onAgreementChange(e: any) {
  form.agreed = e.detail.value.length > 0;
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

  if (!form.agreed) {
    uni.showToast({ title: "请先勾选协议", icon: "none" });
    return false;
  }

  return true;
}

async function handleLogin() {
  if (isLoading.value || !validateForm()) {
    return;
  }

  isLoading.value = true;
  try {
    const result = await userStore.loginWithPassword({
      meow_no: form.meow_no,
      password: form.password,
      captcha_id: form.captcha_id,
      captcha_code: form.captcha_code,
      agree_terms: form.agreed,
    });
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
  } catch (error) {
    const message = error instanceof Error ? error.message : "登录失败";
    uni.showToast({ title: message, icon: "none" });
    await loadCaptcha();
  } finally {
    isLoading.value = false;
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
}

.inline-input {
  flex: 1;
  border: 0;
  box-shadow: none;
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
.login-button::after,
.modal-btn::after {
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

.agreement {
  margin: 28rpx 22rpx 0;
  flex: 0 0 auto;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
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

.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 44rpx;
  box-sizing: border-box;
  background: rgba(28, 42, 30, 0.42);
  backdrop-filter: blur(12rpx);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  position: relative;
  width: 624rpx;
  max-width: 100%;
  min-height: 560rpx;
  box-sizing: border-box;
  padding: 74rpx 48rpx 46rpx;
  border: 2rpx solid rgba(213, 232, 203, 0.96);
  border-radius: 42rpx;
  background:
    radial-gradient(circle at 12% 10%, rgba(207, 236, 194, 0.9) 0, rgba(207, 236, 194, 0) 152rpx),
    radial-gradient(circle at 88% 12%, rgba(255, 235, 208, 0.94) 0, rgba(255, 235, 208, 0) 150rpx),
    linear-gradient(180deg, #ffffff 0%, #fbfff7 100%);
  box-shadow: 0 34rpx 88rpx rgba(19, 55, 24, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  animation: modalShow 0.24s ease-out forwards;
}

@keyframes modalShow {
  from {
    opacity: 0;
    transform: translateY(20rpx) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 16rpx;
  background: linear-gradient(90deg, #d6efc8 0%, #6faf62 54%, #f2cf9f 100%);
}

.modal-card::after {
  content: "";
  position: absolute;
  left: 42rpx;
  right: 42rpx;
  bottom: 132rpx;
  height: 2rpx;
  background: linear-gradient(90deg, rgba(111, 175, 98, 0), rgba(111, 175, 98, 0.28), rgba(111, 175, 98, 0));
}

.modal-corner-paw {
  position: absolute;
  width: 124rpx;
  height: 124rpx;
  opacity: 0.14;
  pointer-events: none;
}

.modal-corner-paw-left {
  left: -24rpx;
  top: 34rpx;
  transform: rotate(-20deg);
}

.modal-corner-paw-right {
  right: -18rpx;
  bottom: 96rpx;
  transform: rotate(18deg);
}

.modal-close {
  position: absolute;
  top: 32rpx;
  right: 32rpx;
  width: 56rpx;
  height: 56rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.76);
  color: #78a26d;
  font-size: 40rpx;
  line-height: 52rpx;
  box-shadow: 0 8rpx 22rpx rgba(42, 83, 48, 0.08);
}

.modal-close::after {
  border: 0;
}

.modal-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
  width: 100%;
  margin-bottom: 42rpx;
}

.paw-icon {
  width: 42rpx;
  height: 42rpx;
}

.left-paw {
  transform: rotate(-18deg);
}

.right-paw {
  transform: rotate(16deg);
}

.modal-title {
  color: #287331;
  font-size: 40rpx;
  font-weight: 800;
  letter-spacing: 4rpx;
  line-height: 1.2;
}

.modal-body {
  position: relative;
  z-index: 1;
  width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 44rpx;
}

.modal-joke-card {
  position: relative;
  width: 100%;
  min-height: 278rpx;
  box-sizing: border-box;
  padding: 24rpx 22rpx 34rpx;
  border: 2rpx solid rgba(224, 237, 215, 0.76);
  border-radius: 32rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86) 0%, rgba(255, 255, 255, 0.66) 100%),
    radial-gradient(circle at 50% 18%, rgba(247, 211, 164, 0.26), rgba(247, 211, 164, 0) 154rpx);
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.modal-cat {
  width: 126rpx;
  height: 126rpx;
  margin-bottom: 10rpx;
  flex: 0 0 auto;
}

.modal-joke-title {
  color: #566a61;
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 38rpx;
  font-weight: 500;
  letter-spacing: 4rpx;
  line-height: 1.35;
  text-align: center;
}

.modal-joke-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 34rpx;
  margin: 12rpx 0 8rpx;
}

.modal-joke-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: rgba(226, 198, 164, 0.62);
}

.modal-joke-leaf {
  width: 28rpx;
  height: 14rpx;
  border-left: 6rpx solid rgba(150, 190, 137, 0.7);
  border-bottom: 6rpx solid rgba(150, 190, 137, 0.7);
  transform: rotate(-45deg);
}

.modal-joke-sub {
  color: #d6c3a6;
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 25rpx;
  letter-spacing: 2rpx;
  line-height: 1.4;
  text-align: center;
}

.modal-btn {
  position: relative;
  z-index: 1;
  width: 286rpx;
  height: 76rpx;
  margin: 0;
  border: 0;
  border-radius: 38rpx;
  background: linear-gradient(90deg, #62af59 0%, #2f8738 100%);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 76rpx;
  box-shadow: 0 14rpx 28rpx rgba(55, 133, 56, 0.24);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.modal-btn::after {
  border: 0;
}

.modal-btn-hover {
  opacity: 0.88;
}

.btn-paw-icon {
  width: 32rpx;
  height: 32rpx;
}
</style>
