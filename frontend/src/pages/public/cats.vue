<template>
  <view class="pub-page" :style="{ '--status-bar-height': statusBarHeight + 'px' }">
    <image class="pub-bg" :src="paperBackground" mode="aspectFill" />
    <view class="pub-bg-wash" />

    <view class="pub-topbar">
      <button class="pub-back" @tap="goBack">‹</button>
    </view>

    <view class="registry-head">
      <text class="registry-h1">校园猫咪</text>
      <text class="pub-eyebrow">在册名录 · 共 {{ total }} 位喵校友</text>
      <view class="filter-tabs">
        <view
          v-for="option in filterOptions"
          :key="option.value"
          class="filter-tab"
          :class="{ 'is-active': activeFilter === option.value }"
          @tap="selectFilter(option.value)"
        >
          <text>{{ option.label }}</text>
        </view>
      </view>
    </view>

    <scroll-view
      class="pub-body"
      scroll-y
      enhanced
      :show-scrollbar="false"
      @scrolltolower="loadMore"
    >
      <view class="pub-content">
        <view v-if="loading && cats.length === 0" class="pub-state">
          <text class="pub-state-emoji">🐾</text>
          <text>正在翻阅名录…</text>
        </view>

        <view v-else-if="!loading && cats.length === 0" class="pub-state">
          <text class="pub-state-emoji">🐱</text>
          <text>{{ errorText || "这一页还没有猫咪" }}</text>
          <button v-if="errorText" class="pub-btn pub-btn-ghost" @tap="reload">重试</button>
        </view>

        <view v-else class="registry-list">
          <view
            v-for="(cat, index) in cats"
            :key="cat.cat_id"
            class="registry-row"
            @tap="goDetail(cat.cat_id)"
          >
            <view class="pub-print registry-print">
              <image class="pub-print-img registry-photo" :src="resolvePublicImage(cat.avatar_url)" mode="aspectFill" />
            </view>
            <view class="registry-body">
              <view class="registry-line">
                <text class="pub-eyebrow">档案 No.{{ padNo(index + 1) }}</text>
                <view class="pub-status registry-status">
                  <view class="pub-status-dot" :class="statusDotClass(cat.status)" />
                  <text>{{ statusLabel(cat.status) }}</text>
                </view>
              </view>
              <view class="registry-name-row">
                <text class="registry-name">{{ cat.name }}</text>
                <text class="registry-sex">{{ sexLabel(cat.sex) }}</text>
              </view>
              <text v-if="cat.alias_summary" class="registry-alias">别名 · {{ cat.alias_summary }}</text>
              <text class="pub-tags">{{ cat.personality_tags.slice(0, 3).join(" · ") }}</text>
            </view>
            <text class="registry-chevron">›</text>
          </view>
        </view>

        <view v-if="cats.length > 0" class="list-foot">
          <text v-if="loading">加载中…</text>
          <text v-else-if="!hasMore">—— 名录到此一页 ——</text>
        </view>
        <view class="pub-safe-bottom" />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { getPublicCats, type PublicCatListItem } from "@/api/public";
import { resolvePublicImage } from "./public-assets";
import { useStatusBarHeight } from "./use-status-bar";

import paperBackground from "../../../素材/加载页素材/背景.jpg";

interface FilterOption {
  label: string;
  value: string;
  status?: string;
}

const filterOptions: FilterOption[] = [
  { label: "全部", value: "all" },
  { label: "在校", value: "active", status: "active" },
  { label: "关注中", value: "watching", status: "watching" },
  { label: "已送养", value: "adopted", status: "adopted" },
];

const PAGE_SIZE = 10;

const { statusBarHeight } = useStatusBarHeight();

const cats = ref<PublicCatListItem[]>([]);
const activeFilter = ref("all");
const page = ref(1);
const total = ref(0);
const hasMore = ref(true);
const loading = ref(false);
const errorText = ref("");

const STATUS_LABELS: Record<string, string> = {
  active: "在校",
  watching: "关注中",
  adopted: "已送养",
};

const SEX_LABELS: Record<string, string> = {
  male: "♂",
  female: "♀",
};

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? "在校";
}

function statusDotClass(status: string): string {
  if (status === "watching") {
    return "is-watching";
  }
  if (status === "adopted") {
    return "is-adopted";
  }
  return "";
}

function sexLabel(sex: string): string {
  return SEX_LABELS[sex] ?? "";
}

function padNo(value: number): string {
  return value < 10 ? `0${value}` : `${value}`;
}

function currentStatus(): string | undefined {
  return filterOptions.find((option) => option.value === activeFilter.value)?.status;
}

async function fetchPage(reset: boolean) {
  if (loading.value) {
    return;
  }
  if (!reset && !hasMore.value) {
    return;
  }

  loading.value = true;
  errorText.value = "";
  const targetPage = reset ? 1 : page.value + 1;

  try {
    const result = await getPublicCats({
      status: currentStatus(),
      page: targetPage,
      page_size: PAGE_SIZE,
    });
    cats.value = reset ? result.items : [...cats.value, ...result.items];
    page.value = result.page;
    total.value = result.total;
    hasMore.value = result.has_more;
  } catch {
    if (reset) {
      cats.value = [];
    }
    errorText.value = "名录加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function selectFilter(value: string) {
  if (activeFilter.value === value) {
    return;
  }
  activeFilter.value = value;
  hasMore.value = true;
  void fetchPage(true);
}

function loadMore() {
  void fetchPage(false);
}

function reload() {
  void fetchPage(true);
}

function goDetail(catId: string) {
  uni.navigateTo({ url: `/pages/public/cat-detail?cat_id=${encodeURIComponent(catId)}` });
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.reLaunch({ url: "/pages/public/home" });
  }
}

onLoad(() => {
  void fetchPage(true);
});
</script>

<style scoped>
@import "./public-theme.css";

.registry-head {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  padding: 8rpx 40rpx 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.registry-h1 {
  font-size: 46rpx;
  font-weight: 800;
  letter-spacing: 3rpx;
  color: #31402b;
}

.filter-tabs {
  display: flex;
  gap: 40rpx;
  margin-top: 8rpx;
  border-bottom: 2rpx dashed rgba(38, 123, 47, 0.28);
}

.filter-tab {
  padding: 10rpx 2rpx 14rpx;
  font-size: 27rpx;
  color: #6d7862;
  border-bottom: 5rpx solid transparent;
  margin-bottom: -2rpx;
}

.filter-tab.is-active {
  color: #267b2f;
  font-weight: 800;
  border-bottom-color: #267b2f;
}

.registry-list {
  display: flex;
  flex-direction: column;
  padding-top: 6rpx;
}

.registry-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 28rpx 0;
  border-bottom: 2rpx dashed rgba(38, 123, 47, 0.22);
}

.registry-row:last-child {
  border-bottom: 0;
}

.registry-print {
  width: 152rpx;
  height: 152rpx;
  flex: 0 0 auto;
}

.registry-photo {
  width: 128rpx;
  height: 128rpx;
}

.registry-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.registry-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.registry-name-row {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
}

.registry-name {
  font-size: 32rpx;
  font-weight: 800;
  color: #31402b;
}

.registry-sex {
  font-size: 27rpx;
  font-weight: 700;
  color: #4f8a47;
}

.registry-status {
  flex: 0 0 auto;
}

.registry-alias {
  font-size: 22rpx;
  color: #6d7862;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.registry-chevron {
  flex: 0 0 auto;
  font-size: 34rpx;
  color: rgba(49, 64, 43, 0.28);
}

.list-foot {
  padding: 32rpx 0 8rpx;
  text-align: center;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: #9aa394;
}
</style>
