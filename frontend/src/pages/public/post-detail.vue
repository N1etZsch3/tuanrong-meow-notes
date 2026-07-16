<template>
  <view class="pub-page" :style="{ '--status-bar-height': statusBarHeight + 'px' }">
    <image class="pub-bg" :src="paperBackground" mode="aspectFill" />
    <view class="pub-bg-wash" />

    <view class="pub-topbar">
      <button class="pub-back" @tap="goBack">‹</button>
      <text class="pub-topbar-title">{{ navTitle }}</text>
    </view>

    <scroll-view class="pub-body" scroll-y>
      <view class="pub-content">
        <view v-if="loading" class="pub-state">
          <text class="pub-state-emoji">📖</text>
          <text>正在翻页…</text>
        </view>

        <view v-else-if="!post" class="pub-state">
          <text class="pub-state-emoji">📭</text>
          <text>{{ errorText || "找不到这篇内容" }}</text>
          <button class="pub-btn pub-btn-ghost" @tap="goBack">返回</button>
        </view>

        <template v-else>
          <text class="post-eyebrow">{{ typeLabel }}<text v-if="post.published_at"> · {{ post.published_at }}</text></text>
          <text class="post-title">{{ post.title }}</text>

          <view v-if="post.cover_url" class="album-wrap">
            <view class="pub-print cover-print">
              <view class="pub-tape" />
              <image class="pub-print-img cover-img" :src="resolvePublicImage(post.cover_url)" mode="aspectFill" />
            </view>
          </view>

          <view class="post-content">
            <block v-for="(block, index) in post.blocks" :key="index">
              <text v-if="block.block_type === 'text' && block.text" class="content-text">{{ block.text }}</text>
              <view v-else-if="block.block_type === 'image' && block.image_url" class="pub-print content-print">
                <view class="pub-tape" />
                <image class="pub-print-img content-img" :src="resolvePublicImage(block.image_url)" mode="widthFix" />
              </view>
            </block>
          </view>

          <view v-if="post.post_type === 'merch'" class="merch-note">
            <text>该周边为社团活动纪念品，仅用于展示，不对外销售。</text>
          </view>

          <view class="post-foot">
            <text>—— 团绒猫协 ——</text>
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

import { getPublicPostDetail, type PublicPostDetail } from "@/api/public";
import { resolvePublicImage } from "./public-assets";
import { useStatusBarHeight } from "./use-status-bar";

import paperBackground from "../../../素材/加载页素材/背景.jpg";

const post = ref<PublicPostDetail | null>(null);
const loading = ref(true);
const errorText = ref("");

const { statusBarHeight } = useStatusBarHeight();

const typeLabel = computed(() =>
  post.value?.post_type === "merch" ? "猫协周边" : "协会趣事",
);
const navTitle = computed(() =>
  post.value?.post_type === "merch" ? "周边详情" : "趣事详情",
);

async function loadPost(postId: string) {
  loading.value = true;
  errorText.value = "";
  try {
    post.value = await getPublicPostDetail(postId);
  } catch {
    post.value = null;
    errorText.value = "内容加载失败";
  } finally {
    loading.value = false;
  }
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.reLaunch({ url: "/pages/public/home" });
  }
}

onLoad((query) => {
  const postId = typeof query?.post_id === "string" ? query.post_id : "";
  if (!postId) {
    loading.value = false;
    errorText.value = "缺少内容信息";
    return;
  }
  void loadPost(postId);
});
</script>

<style scoped>
@import "./public-theme.css";

.post-eyebrow {
  display: block;
  margin-top: 16rpx;
  font-size: 22rpx;
  letter-spacing: 3rpx;
  color: #267b2f;
  font-weight: 700;
}

.post-title {
  display: block;
  margin-top: 14rpx;
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.4;
  letter-spacing: 1rpx;
  color: #31402b;
}

.album-wrap {
  margin-top: 30rpx;
}

.cover-print {
  width: 100%;
  transform: rotate(-0.6deg);
}

.cover-img {
  width: 100%;
  height: 420rpx;
}

.post-content {
  margin-top: 34rpx;
  display: flex;
  flex-direction: column;
  gap: 26rpx;
}

.content-text {
  font-size: 29rpx;
  line-height: 2;
  letter-spacing: 0.5rpx;
  color: #414f39;
}

.content-print {
  width: 100%;
  margin-top: 8rpx;
  transform: rotate(0.8deg);
}

.content-img {
  width: 100%;
}

.merch-note {
  margin-top: 30rpx;
  padding: 22rpx 26rpx;
  border-left: 4rpx solid rgba(201, 143, 43, 0.6);
  background: rgba(201, 143, 43, 0.08);
  font-size: 24rpx;
  line-height: 1.7;
  color: #99701f;
}

.post-foot {
  padding: 48rpx 0 8rpx;
  text-align: center;
  font-size: 23rpx;
  letter-spacing: 4rpx;
  color: #9aa394;
}
</style>
