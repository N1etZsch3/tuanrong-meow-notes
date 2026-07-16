<template>
  <view class="help-page">
    <image class="page-bg" :src="pageBackground" mode="aspectFill" />
    <scroll-view class="help-scroll" scroll-y :show-scrollbar="false">
      <view class="help-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="nav-copy">
            <text class="nav-title">帮助与反馈</text>
            <text class="nav-subtitle">常见问题与联系方式</text>
          </view>
        </view>

        <view class="help-section">
          <text class="section-title">常见问题</text>
          <view class="faq-group">
            <view
              v-for="(item, index) in faqItems"
              :key="index"
              class="faq-item"
            >
              <text class="faq-question">{{ item.question }}</text>
              <text class="faq-answer">{{ item.answer }}</text>
            </view>
          </view>
        </view>

        <view class="help-section">
          <text class="section-title">联系我们</text>
          <view class="contact-group">
            <view
              v-for="(item, index) in contactItems"
              :key="index"
              class="contact-row"
            >
              <text class="contact-label">{{ item.label }}</text>
              <text class="contact-value">{{ item.value }}</text>
            </view>
          </view>
          <text class="help-notice">{{ notice }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import {
  HELP_CONTACT_ITEMS,
  HELP_FAQ_ITEMS,
  HELP_FEEDBACK_NOTICE,
} from "./help-feedback";
import pageBackground from "../../../素材/加载页素材/背景.jpg";

const faqItems = HELP_FAQ_ITEMS;
const contactItems = HELP_CONTACT_ITEMS;
const notice = HELP_FEEDBACK_NOTICE;

function goBack() {
  uni.navigateBack();
}
</script>

<style scoped>
.help-page {
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

.help-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.help-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
  margin-bottom: 40rpx;
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

.back-button::after {
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

.help-section + .help-section {
  margin-top: 30rpx;
}

.section-title {
  display: block;
  margin: 0 18rpx 12rpx;
  color: #6f7781;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
}

.faq-group,
.contact-group {
  overflow: hidden;
  border: 1rpx solid rgba(207, 218, 208, 0.72);
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8rpx 24rpx rgba(42, 63, 43, 0.07);
}

.faq-item {
  box-sizing: border-box;
  padding: 26rpx 24rpx;
}

.faq-item + .faq-item {
  border-top: 1rpx solid rgba(210, 218, 213, 0.74);
}

.faq-question {
  display: block;
  color: #22272f;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.4;
}

.faq-answer {
  display: block;
  margin-top: 12rpx;
  color: #59616c;
  font-size: 25rpx;
  line-height: 1.6;
}

.contact-row {
  box-sizing: border-box;
  min-height: 88rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.contact-row + .contact-row {
  border-top: 1rpx solid rgba(210, 218, 213, 0.74);
}

.contact-label {
  color: #22272f;
  font-size: 27rpx;
  font-weight: 900;
}

.contact-value {
  min-width: 0;
  color: #59616c;
  font-size: 25rpx;
  text-align: right;
}

.help-notice {
  display: block;
  margin: 20rpx 18rpx 0;
  color: #7a828c;
  font-size: 23rpx;
  line-height: 1.6;
}
</style>
