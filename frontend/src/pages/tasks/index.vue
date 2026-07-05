<template>
  <view class="meow-notes-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="page-inner">
      <view class="page-head">
        <view class="title-copy">
          <view class="title-row">
            <text class="title-text">喵记</text>
            <image class="title-icon" :src="pawIcon" mode="aspectFit" />
          </view>
          <text class="title-subtitle">记录与管理入口</text>
        </view>
        <view class="head-actions">
          <button class="round-action" hover-class="button-hover" @tap="goSearch">
            <text class="round-icon">⌕</text>
          </button>
          <button class="round-action" hover-class="button-hover" @tap="showMore">
            <text class="round-icon">…</text>
          </button>
        </view>
      </view>

      <view class="meow-shelf">
        <view class="shelf-panel">
          <button
            v-for="book in noteBooks"
            :key="book.key"
            class="note-book"
            :class="`note-book-${book.tone}`"
            hover-class="book-hover"
            @tap="openBook(book)"
          >
            <view class="book-spine" />
            <view class="book-ribbon" />
            <view class="book-label">
              <text>{{ book.label }}</text>
            </view>
            <image class="book-icon" :src="book.icon" mode="aspectFit" />
          </button>
          <view class="shelf-board shelf-board-top" />
          <view class="shelf-board shelf-board-middle" />
          <view class="shelf-board shelf-board-bottom" />
        </view>
      </view>

      <button class="summary-strip" hover-class="button-hover" @tap="goSearch">
        <image class="summary-leaf" :src="pawIcon" mode="aspectFit" />
        <text class="summary-copy">最近新增 4 条记录 · 今日待处理 3 项</text>
        <text class="summary-arrow">›</text>
      </button>
    </view>
    <AppTabBar active-key="tasks" />
  </view>
</template>

<script setup lang="ts">
import AppTabBar from "@/components/AppTabBar.vue";

import taskIcon from "../../../素材/png/地图点/日常任务.png";
import supplyIcon from "../../../素材/png/地图点/物资点.png";
import landmarkIcon from "../../../素材/png/地图点/地标.png";
import medicineIcon from "../../../素材/png/地图点/医疗任务.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

interface NoteBook {
  key: string;
  label: string;
  icon: string;
  tone: "sage" | "cream" | "yellow";
  url?: string;
}

const noteBooks: NoteBook[] = [
  {
    key: "tasks",
    label: "任务",
    icon: taskIcon,
    tone: "sage",
    url: "/pages/tasks/list",
  },
  {
    key: "supplies",
    label: "物资",
    icon: supplyIcon,
    tone: "cream",
    url: "/pages/supplies/index",
  },
  {
    key: "landmarks",
    label: "校园地标",
    icon: landmarkIcon,
    tone: "sage",
    url: "/pages/landmarks/index",
  },
  {
    key: "medicine",
    label: "药品",
    icon: medicineIcon,
    tone: "yellow",
  },
];

function openBook(book: NoteBook) {
  if (!book.url) {
    uni.showToast({
      title: "药品管理暂未开放",
      icon: "none",
    });
    return;
  }

  uni.navigateTo({ url: book.url });
}

function goSearch() {
  uni.navigateTo({ url: "/pages/tasks/list" });
}

function showMore() {
  uni.showToast({
    title: "更多喵记工具建设中",
    icon: "none",
  });
}
</script>

<style scoped>
.meow-notes-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: #243d28;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.page-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) 32rpx
    calc(env(safe-area-inset-bottom) + 170rpx);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
  padding: 0 18rpx;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.title-text {
  color: #2f6333;
  font-size: 64rpx;
  font-weight: 900;
  line-height: 1;
}

.title-icon {
  width: 48rpx;
  height: 48rpx;
}

.title-subtitle {
  display: block;
  margin-top: 18rpx;
  color: #6d786f;
  font-size: 25rpx;
  font-weight: 800;
}

.head-actions {
  display: flex;
  gap: 22rpx;
  padding-top: 18rpx;
}

.round-action,
.summary-strip,
.note-book {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
}

.round-action::after,
.summary-strip::after,
.note-book::after {
  border: 0;
}

.round-action {
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 15rpx 30rpx rgba(40, 73, 42, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
}

.round-icon {
  color: #2f6333;
  font-size: 46rpx;
  font-weight: 900;
  line-height: 1;
}

.meow-shelf {
  box-sizing: border-box;
  margin-top: 46rpx;
  border: 2rpx solid rgba(205, 183, 148, 0.55);
  border-radius: 36rpx;
  padding: 22rpx;
  background: rgba(250, 238, 218, 0.92);
  box-shadow: 0 18rpx 36rpx rgba(98, 79, 45, 0.11);
}

.shelf-panel {
  position: relative;
  box-sizing: border-box;
  min-height: 850rpx;
  border: 2rpx solid rgba(199, 166, 116, 0.42);
  border-radius: 26rpx;
  padding: 44rpx 28rpx;
  background: linear-gradient(90deg, rgba(236, 205, 159, 0.72), rgba(244, 220, 180, 0.8));
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-content: start;
  column-gap: 26rpx;
  row-gap: 118rpx;
}

.shelf-board {
  position: absolute;
  left: 0;
  right: 0;
  height: 38rpx;
  border: 2rpx solid rgba(211, 188, 148, 0.78);
  background: linear-gradient(180deg, #fffbea, #efe5c9);
  box-shadow: 0 8rpx 12rpx rgba(128, 94, 45, 0.12);
}

.shelf-board-top {
  top: 270rpx;
}

.shelf-board-middle {
  top: 590rpx;
}

.shelf-board-bottom {
  bottom: 22rpx;
}

.note-book {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  width: 100%;
  height: 248rpx;
  overflow: hidden;
  border: 2rpx solid rgba(102, 135, 85, 0.28);
  border-radius: 14rpx 20rpx 20rpx 14rpx;
  box-shadow: inset 8rpx 0 0 rgba(102, 157, 91, 0.86), 0 8rpx 16rpx rgba(92, 72, 43, 0.13);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.note-book-sage {
  background: linear-gradient(180deg, #e7f0d9, #dceacb);
}

.note-book-cream {
  background: linear-gradient(180deg, #fffaf0, #f5eddd);
}

.note-book-yellow {
  background: linear-gradient(180deg, #fff5ca, #f8e8a8);
}

.book-hover,
.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.book-spine {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 20rpx;
  width: 3rpx;
  background: rgba(84, 122, 72, 0.26);
}

.book-ribbon {
  position: absolute;
  top: 0;
  right: 26rpx;
  width: 30rpx;
  height: 52rpx;
  background: #9fbd80;
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 78%, 0 100%);
}

.book-label {
  box-sizing: border-box;
  max-width: 126rpx;
  min-height: 60rpx;
  margin-top: 58rpx;
  border: 2rpx solid rgba(204, 190, 161, 0.76);
  border-radius: 9rpx;
  padding: 0 12rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #111827;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 60rpx;
  text-align: center;
}

.book-label text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-icon {
  width: 72rpx;
  height: 72rpx;
  margin-top: 36rpx;
  opacity: 0.78;
}

.summary-strip {
  box-sizing: border-box;
  width: 100%;
  min-height: 76rpx;
  margin-top: 28rpx;
  border: 2rpx solid rgba(203, 217, 190, 0.82);
  border-radius: 26rpx;
  padding: 0 22rpx;
  background: rgba(249, 252, 241, 0.9);
  box-shadow: 0 12rpx 28rpx rgba(39, 76, 42, 0.07);
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.summary-leaf {
  width: 38rpx;
  height: 38rpx;
  flex: 0 0 auto;
}

.summary-copy {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-arrow {
  color: #8d967f;
  font-size: 52rpx;
  font-weight: 700;
  line-height: 1;
}
</style>
