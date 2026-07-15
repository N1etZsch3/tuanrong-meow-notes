<template>
  <view class="pub-page" :style="{ '--status-bar-height': statusBarHeight + 'px' }">
    <image class="pub-bg" :src="paperBackground" mode="aspectFill" />
    <view class="pub-bg-wash" />

    <view class="pub-topbar">
      <button class="pub-back" @tap="goBack">‹</button>
      <text class="pub-topbar-title">猫咪档案</text>
    </view>

    <scroll-view class="pub-body" scroll-y>
      <view class="pub-content">
        <view v-if="loading" class="pub-state">
          <text class="pub-state-emoji">🐾</text>
          <text>正在调取档案…</text>
        </view>

        <view v-else-if="!cat" class="pub-state">
          <text class="pub-state-emoji">🙀</text>
          <text>{{ errorText || "找不到这份猫咪档案" }}</text>
          <button class="pub-btn pub-btn-ghost" @tap="goBack">返回</button>
        </view>

        <template v-else>
          <!-- taped-in hero photo(s) -->
          <view class="album-wrap">
            <view class="pub-print album-print">
              <view class="pub-tape" />
              <swiper
                v-if="photos.length > 1"
                class="album-swiper"
                :indicator-dots="true"
                indicator-color="rgba(251, 252, 244, 0.6)"
                indicator-active-color="#fbfcf4"
                circular
              >
                <swiper-item v-for="(photo, index) in photos" :key="index">
                  <image class="album-img" :src="resolvePublicImage(photo.file_url)" mode="aspectFill" />
                </swiper-item>
              </swiper>
              <image
                v-else-if="photos.length === 1"
                class="album-img"
                :src="resolvePublicImage(photos[0].file_url)"
                mode="aspectFill"
              />
              <view v-else class="album-img album-empty">
                <text class="pub-state-emoji">🐱</text>
              </view>
            </view>
            <text v-if="currentCaption" class="album-caption">{{ currentCaption }}</text>
          </view>

          <!-- registry fields -->
          <view class="file-head">
            <text class="file-name">{{ cat.name }}</text>
            <text class="file-sex">{{ sexLabel(cat.sex) }}</text>
            <view class="pub-status file-status">
              <view class="pub-status-dot" :class="statusDotClass(cat.status)" />
              <text>{{ statusLabel(cat.status) }}</text>
            </view>
          </view>

          <view class="file-rows">
            <view v-if="aliasText" class="file-row">
              <text class="file-label">别名</text>
              <text class="file-value">{{ aliasText }}</text>
            </view>
            <view class="file-row">
              <text class="file-label">毛色</text>
              <text class="file-value">{{ coatLabel(cat.coat_color) }}</text>
            </view>
            <view class="file-row">
              <text class="file-label">绝育</text>
              <text class="file-value">{{ neuterLabel(cat.neuter_status) }}</text>
            </view>
            <view v-if="cat.personality_tags.length" class="file-row">
              <text class="file-label">性格</text>
              <text class="file-tags">{{ cat.personality_tags.join(" · ") }}</text>
            </view>
          </view>

          <template v-if="cat.story">
            <view class="pub-stitch" />
            <view class="pub-toc">
              <text class="pub-toc-title">猫咪故事</text>
              <view class="pub-toc-leader" />
            </view>
            <text class="story-text">{{ cat.story }}</text>
          </template>

          <view class="privacy-note">
            <text>🐾 为了猫咪安全，具体位置信息不对外公开</text>
          </view>
        </template>

        <view class="pub-safe-bottom" />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { getPublicCatDetail, type PublicCatDetail } from "@/api/public";
import { resolvePublicImage } from "./public-assets";
import { useStatusBarHeight } from "./use-status-bar";

import paperBackground from "../../../素材/加载页素材/背景.jpg";

const cat = ref<PublicCatDetail | null>(null);
const loading = ref(true);
const errorText = ref("");

const { statusBarHeight } = useStatusBarHeight();

const photos = computed(() => cat.value?.photos ?? []);
const currentCaption = computed(() => photos.value[0]?.caption ?? "");
const aliasText = computed(() =>
  cat.value?.aliases.length ? cat.value.aliases.join("、") : "",
);

const STATUS_LABELS: Record<string, string> = {
  active: "在校",
  watching: "关注中",
  adopted: "已送养",
};
const SEX_LABELS: Record<string, string> = { male: "♂", female: "♀" };
const NEUTER_LABELS: Record<string, string> = {
  neutered: "已绝育",
  pending: "待绝育",
  unknown: "未知",
};
const COAT_LABELS: Record<string, string> = {
  orange: "橘色",
  white: "白色",
  black: "黑色",
  gray: "灰色",
  calico: "三花",
  black_white: "奶牛",
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
function neuterLabel(status: string): string {
  return NEUTER_LABELS[status] ?? "未知";
}
function coatLabel(color: string): string {
  return COAT_LABELS[color] ?? color;
}

async function loadCat(catId: string) {
  loading.value = true;
  errorText.value = "";
  try {
    cat.value = await getPublicCatDetail(catId);
  } catch {
    cat.value = null;
    errorText.value = "档案加载失败";
  } finally {
    loading.value = false;
  }
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.reLaunch({ url: "/pages/public/cats" });
  }
}

onLoad((query) => {
  const catId = typeof query?.cat_id === "string" ? query.cat_id : "";
  if (!catId) {
    loading.value = false;
    errorText.value = "缺少猫咪信息";
    return;
  }
  void loadCat(catId);
});
</script>

<style scoped>
@import "./public-theme.css";

.album-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 22rpx;
}

.album-print {
  width: 100%;
  transform: rotate(-0.8deg);
}

.album-swiper,
.album-img {
  display: block;
  width: 100%;
  height: 500rpx;
}

.album-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #edf2e4;
}

.album-caption {
  margin-top: 16rpx;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: #6d7862;
}

.file-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 34rpx;
}

.file-name {
  font-size: 44rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
  color: #31402b;
  line-height: 1.2;
}

.file-sex {
  font-size: 30rpx;
  font-weight: 700;
  color: #4f8a47;
}

.file-status {
  margin-left: auto;
}

.file-rows {
  margin-top: 22rpx;
  display: flex;
  flex-direction: column;
}

.file-row {
  display: flex;
  align-items: baseline;
  gap: 24rpx;
  padding: 16rpx 0;
  border-bottom: 2rpx dotted rgba(49, 64, 43, 0.18);
}

.file-row:last-child {
  border-bottom: 0;
}

.file-label {
  flex: 0 0 auto;
  font-size: 24rpx;
  letter-spacing: 4rpx;
  color: #6d7862;
}

.file-value {
  font-size: 27rpx;
  font-weight: 600;
  color: #31402b;
}

.file-tags {
  font-size: 26rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
  color: #267b2f;
}

.story-text {
  display: block;
  font-size: 28rpx;
  line-height: 1.95;
  letter-spacing: 0.5rpx;
  color: #414f39;
}

.privacy-note {
  margin-top: 44rpx;
  text-align: center;
  font-size: 22rpx;
  letter-spacing: 1rpx;
  color: #9aa394;
}
</style>
