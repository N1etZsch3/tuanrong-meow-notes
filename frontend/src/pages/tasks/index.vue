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
      </view>

      <view class="shelf" aria-label="书架">
        <view class="shelf__inner">
          <view v-for="(row, rowIndex) in currentBookRows" :key="rowIndex" class="cell">
            <view class="cell__books">
              <view
                v-for="book in row"
                :key="book.key"
                class="book"
                :class="[
                  `book--${book.tone}`,
                  { 'book--ribbon': book.ribbon },
                ]"
                @tap="openBook(book)"
              >
                <view class="book__label">
                  <text>{{ book.label }}</text>
                </view>
                <image class="book__icon" :src="book.icon" mode="aspectFit" />
              </view>
            </view>
            <view class="board"></view>
          </view>
        </view>
      </view>

      <view class="shelf-pager" aria-label="书架分页">
        <button
          class="pager-button"
          :class="{ 'pager-button--disabled': !canGoPreviousBookPage }"
          :disabled="!canGoPreviousBookPage"
          @tap="goPreviousBookPage"
        >
          上一页
        </button>
        <view class="pager-count">
          <text>{{ currentShelfPageLabel }}</text>
        </view>
        <button
          class="pager-button"
          :class="{ 'pager-button--disabled': !canGoNextBookPage }"
          :disabled="!canGoNextBookPage"
          @tap="goNextBookPage"
        >
          下一页
        </button>
      </view>
    </view>
    <AppTabBar active-key="tasks" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import AppTabBar from "@/components/AppTabBar.vue";

import taskIcon from "../../../素材/svg/喵记/任务.svg";
import supplyIcon from "../../../素材/svg/喵记/物资仓库.svg";
import landmarkIcon from "../../../素材/svg/喵记/地标.svg";
import medicineIcon from "../../../素材/svg/喵记/药品.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

interface NoteBook {
  key: string;
  label: string;
  icon: string;
  tone: "green" | "cream" | "mint" | "yellow";
  ribbon: boolean;
  url?: string;
}

const noteBooks: NoteBook[] = [
  {
    key: "tasks",
    label: "任务",
    icon: taskIcon,
    tone: "green",
    ribbon: false,
    url: "/pages/tasks/list",
  },
  {
    key: "supplies",
    label: "物资",
    icon: supplyIcon,
    tone: "cream",
    ribbon: true,
    url: "/pages/supplies/index",
  },
  {
    key: "landmarks",
    label: "校园地标",
    icon: landmarkIcon,
    tone: "mint",
    ribbon: true,
    url: "/pages/landmarks/index",
  },
  {
    key: "medicine",
    label: "药品",
    icon: medicineIcon,
    tone: "yellow",
    ribbon: true,
  },
];

const bookPages: NoteBook[][] = [noteBooks];
const currentBookPage = ref(0);

const totalBookPages = computed(() => bookPages.length);
const currentBookRows = computed(() => buildBookRows(bookPages[currentBookPage.value] ?? []));
const currentShelfPageLabel = computed(
  () => `${currentBookPage.value + 1}/${totalBookPages.value}`,
);
const canGoPreviousBookPage = computed(() => currentBookPage.value > 0);
const canGoNextBookPage = computed(() => currentBookPage.value < totalBookPages.value - 1);

function buildBookRows(books: NoteBook[]): NoteBook[][] {
  return [books.slice(0, 3), books.slice(3, 4), []];
}

function goPreviousBookPage() {
  if (!canGoPreviousBookPage.value) {
    return;
  }

  currentBookPage.value -= 1;
}

function goNextBookPage() {
  if (!canGoNextBookPage.value) {
    return;
  }

  currentBookPage.value += 1;
}

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
  padding: var(--catmap-page-title-top, 92rpx) 28rpx
    calc(env(safe-area-inset-bottom) + 170rpx);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 24rpx;
  padding: 0 22rpx;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
}

.title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

/* 喵记书架组件：迁移自 test/组件/书架书本.html */
.shelf {
  --bg-1: #f7f3e4;
  --bg-2: #eef0dc;
  --frame-1: #f8ead0;
  --frame-2: #eedbb2;
  --panel-1: #dcbd8c;
  --panel-2: #ecd8ae;
  --board-face-1: #fcf3de;
  --board-face-2: #eedcb4;
  --board-top-1: #c9a674;
  --board-top-2: #e9d3a6;
  --shade: 92, 62, 26;
  --ribbon-1: #7fa05a;
  --ribbon-2: #90b06b;
  --book-w: 90px;
  --book-h: calc(134px + 20rpx);
  box-sizing: border-box;
  width: 100%;
  max-width: 388px;
  margin: 46rpx auto 0;
  padding: 18px 18px 30px;
  border-radius: 30px;
  background: linear-gradient(180deg, var(--frame-1) 0%, #f3e2be 60%, var(--frame-2) 100%);
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.55),
    inset 0 -3px 0 rgba(var(--shade), 0.12),
    0 6px 14px -6px rgba(var(--shade), 0.28),
    0 26px 48px -20px rgba(var(--shade), 0.38);
}

.shelf__inner {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(146, 108, 58, 0.2);
}

.cell {
  display: flex;
  flex-direction: column;
  background: linear-gradient(
    180deg,
    var(--panel-1) 0%,
    #e7d0a4 22%,
    var(--panel-2) 70%,
    #e3c99a 100%
  );
  box-shadow:
    inset 0 18px 22px -14px rgba(var(--shade), 0.5),
    inset 12px 0 16px -12px rgba(var(--shade), 0.3),
    inset -12px 0 16px -12px rgba(var(--shade), 0.3),
    inset 0 -10px 12px -10px rgba(var(--shade), 0.28);
}

.cell__books {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: calc(154px + 40rpx);
  padding: 0 15px;
}

.board {
  position: relative;
  z-index: 1;
  height: 17px;
  background: linear-gradient(180deg, var(--board-face-1), var(--board-face-2));
  border-radius: 3px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -2px 3px -2px rgba(150, 110, 60, 0.35),
    0 5px 7px -3px rgba(var(--shade), 0.4),
    0 11px 16px -8px rgba(var(--shade), 0.28);
}

.board::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: -7px;
  height: 7px;
  background: linear-gradient(180deg, var(--board-top-1), var(--board-top-2));
  border-radius: 2px 2px 0 0;
  box-shadow: inset 0 1px 0 rgba(var(--shade), 0.25);
}

.book {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  box-sizing: border-box;
  width: var(--book-w);
  height: var(--book-h);
  border-radius: 8px 16px 16px 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 26%),
    linear-gradient(
      90deg,
      var(--spine) 0 11px,
      rgba(87, 72, 35, 0.18) 11px 12px,
      rgba(255, 255, 255, 0.38) 12px 13.5px,
      rgba(255, 255, 255, 0) 13.5px
    ),
    linear-gradient(180deg, var(--cover-hi), var(--cover) 55%, var(--cover-lo));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    inset -3px 0 6px -3px rgba(110, 78, 38, 0.18),
    inset 0 -4px 8px -4px rgba(110, 78, 38, 0.22),
    0 2px 3px -1px rgba(89, 60, 26, 0.35),
    5px 10px 18px -8px rgba(89, 60, 26, 0.38);
}

.book::after {
  content: "";
  position: absolute;
  z-index: -1;
  left: 5px;
  right: 5px;
  bottom: -3px;
  height: 7px;
  border-radius: 50%;
  background: radial-gradient(
    50% 50% at 50% 50%,
    rgba(70, 48, 20, 0.4),
    rgba(70, 48, 20, 0) 72%
  );
  filter: blur(1.5px);
}

.book--ribbon::before {
  content: "";
  position: absolute;
  top: 0;
  right: 15px;
  width: 15px;
  height: 36px;
  background:
    linear-gradient(
      90deg,
      rgba(58, 80, 30, 0.25),
      rgba(58, 80, 30, 0) 30% 70%,
      rgba(58, 80, 30, 0.25)
    ),
    linear-gradient(180deg, var(--ribbon-1), var(--ribbon-2));
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% calc(100% - 7px), 0 100%);
  filter: drop-shadow(0 2px 2px rgba(var(--shade), 0.28));
}

.book--green {
  --cover-hi: #d9e6bf;
  --cover: #cddcac;
  --cover-lo: #c3d49e;
  --spine: #b6ca8f;
}

.book--mint {
  --cover-hi: #e4edcd;
  --cover: #d8e5bd;
  --cover-lo: #cfdfae;
  --spine: #c3d49c;
}

.book--cream {
  --cover-hi: #fbf6e7;
  --cover: #f7f0da;
  --cover-lo: #f0e7c9;
  --spine: #d6e0b4;
}

.book--yellow {
  --cover-hi: #f9ecc0;
  --cover: #f4e3a8;
  --cover-lo: #edd894;
  --spine: #e0cb80;
}

.book__label {
  position: relative;
  z-index: 2;
  box-sizing: border-box;
  max-width: 76px;
  min-height: 29px;
  margin: 40px auto 0;
  padding: 0 5px;
  border: 1px solid rgba(204, 190, 161, 0.76);
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.88);
  color: #111827;
  font-size: 14px;
  font-weight: 900;
  line-height: 29px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(var(--shade), 0.12);
}

.book__label text {
  display: block;
  white-space: nowrap;
}

.book__icon {
  position: relative;
  z-index: 2;
  display: block;
  width: 46px;
  height: 46px;
  margin: 24px auto 0;
  object-fit: contain;
  opacity: 0.82;
  filter: brightness(0) saturate(100%) invert(34%) sepia(18%) saturate(1068%)
    hue-rotate(51deg) brightness(92%) contrast(86%);
}

.shelf-pager {
  box-sizing: border-box;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 18rpx;
  width: 100%;
  max-width: 388px;
  min-height: 82rpx;
  margin: 22rpx auto 0;
  padding: 0 14rpx;
}

/* 恢复分页外框时，把这些声明放回 .shelf-pager：
   padding: 10rpx 14rpx;
   border: 2rpx solid rgba(207, 179, 127, 0.62);
   border-radius: 999rpx;
   background:
     linear-gradient(180deg, rgba(255, 252, 241, 0.94), rgba(239, 218, 177, 0.92)),
     linear-gradient(90deg, rgba(252, 243, 222, 0.75), rgba(225, 194, 141, 0.42));
   box-shadow:
     inset 0 3rpx 0 rgba(255, 255, 255, 0.82),
     inset 0 -5rpx 8rpx rgba(126, 83, 37, 0.1),
     0 12rpx 22rpx -12rpx rgba(92, 62, 26, 0.42),
     0 22rpx 44rpx -28rpx rgba(49, 88, 52, 0.28);
*/

.pager-button {
  box-sizing: border-box;
  height: 58rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #fbf3de, #e6ca93);
  color: #5b4124;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 58rpx;
  text-align: center;
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.74),
    inset 0 -4rpx 8rpx rgba(112, 77, 35, 0.16),
    0 7rpx 12rpx -7rpx rgba(88, 58, 25, 0.48);
}

.pager-button::after {
  border: 0;
}

.pager-button--disabled {
  color: rgba(91, 65, 36, 0.42);
  background: linear-gradient(180deg, #f6ebd2, #dec596);
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.52),
    inset 0 -3rpx 6rpx rgba(112, 77, 35, 0.08);
}

.pager-count {
  min-width: 96rpx;
  height: 58rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #d9c294, #f7e7bd 45%, #caa971);
  color: #2f6333;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 58rpx;
  text-align: center;
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.72),
    inset 0 -4rpx 8rpx rgba(93, 61, 28, 0.14),
    0 8rpx 14rpx -9rpx rgba(91, 62, 28, 0.5);
}
</style>
