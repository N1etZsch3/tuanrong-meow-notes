<template>
  <view class="pub-page" :style="{ '--status-bar-height': statusBarHeight + 'px' }">
    <image class="pub-bg" :src="paperBackground" mode="aspectFill" />
    <view class="pub-bg-wash" />

    <view class="pub-topbar">
      <text class="pub-topbar-title">团绒喵记本</text>
    </view>

    <scroll-view class="pub-body" scroll-y>
      <view class="pub-content">
        <!-- Brand opening: the notebook cover page -->
        <view class="hero">
          <image class="hero-cat" :src="catIllustration" mode="aspectFit" />
          <image class="hero-wordmark" :src="appWordmark" mode="aspectFit" />
          <text class="hero-tagline">{{ site?.slogan || "记录每一次温暖的相遇" }}</text>
          <text class="hero-sub">{{ heroSubline }}</text>

          <view class="hero-entry" @tap="isLoggedIn ? goWorkspace() : goLogin()">
            <text>{{ isLoggedIn ? "返回工作区" : "成员入口" }}</text>
            <text class="hero-entry-arrow">›</text>
          </view>
        </view>

        <!-- Registry stats: numbers pressed straight onto the paper -->
        <view class="ledger">
          <view v-if="statsLoading" class="ledger-loading">正在翻开手记…</view>
          <view v-else-if="stats" class="ledger-row">
            <view class="ledger-cell">
              <text class="ledger-num">{{ stats.in_campus_cats }}</text>
              <text class="ledger-label">在册喵校友</text>
            </view>
            <view class="ledger-rule" />
            <view class="ledger-cell">
              <text class="ledger-num">{{ neuterPercent }}<text class="ledger-unit">%</text></text>
              <text class="ledger-label">绝育率</text>
            </view>
            <view class="ledger-rule" />
            <view class="ledger-cell">
              <text class="ledger-num">{{ stats.adopted_cats }}</text>
              <text class="ledger-label">累计送养</text>
            </view>
          </view>
          <view v-else class="ledger-loading">手记数据暂不可用</view>
        </view>

        <view class="pub-stitch" />

        <!-- Campus cats: taped photo prints -->
        <view class="pub-toc">
          <text class="pub-toc-title">校园猫咪</text>
          <view class="pub-toc-leader" />
          <text class="pub-toc-action" @tap="goCats">查看全部 ›</text>
        </view>

        <view v-if="catsLoading" class="pub-state">
          <text class="pub-state-emoji">🐾</text>
          <text>正在唤醒猫咪…</text>
        </view>
        <scroll-view v-else-if="cats.length" class="rail" scroll-x :show-scrollbar="false">
          <view class="rail-track">
            <view
              v-for="(cat, index) in cats"
              :key="cat.cat_id"
              class="rail-item"
              :class="index % 2 === 0 ? 'tilt-left' : 'tilt-right'"
              @tap="goCatDetail(cat.cat_id)"
            >
              <view class="pub-print rail-print">
                <view v-if="index === 0" class="pub-tape" />
                <image class="pub-print-img rail-photo" :src="resolvePublicImage(cat.avatar_url)" mode="aspectFill" />
              </view>
              <text class="rail-no">档案 No.{{ padNo(index + 1) }}</text>
              <text class="rail-name">{{ cat.name }}</text>
              <text class="pub-tags">{{ cat.personality_tags.slice(0, 2).join(" · ") }}</text>
            </view>
          </view>
        </scroll-view>
        <view v-else class="pub-state"><text>暂无猫咪档案</text></view>

        <view class="pub-stitch" />

        <!-- Trivia: editorial index rows -->
        <view class="pub-toc">
          <text class="pub-toc-title">协会趣事</text>
          <view class="pub-toc-leader" />
        </view>

        <view v-if="triviaLoading" class="pub-state"><text>加载中…</text></view>
        <view v-else-if="trivia.length" class="story-list">
          <view
            v-for="post in trivia"
            :key="post.post_id"
            class="story-row"
            @tap="goPostDetail(post.post_id)"
          >
            <view class="pub-print story-print">
              <image class="pub-print-img story-photo" :src="resolvePublicImage(post.cover_url)" mode="aspectFill" />
            </view>
            <view class="story-body">
              <text class="story-title">{{ post.title }}</text>
              <text class="story-summary">{{ post.summary }}</text>
              <text class="pub-eyebrow">{{ post.published_at }}</text>
            </view>
          </view>
        </view>
        <view v-else class="pub-state"><text>暂无趣事，敬请期待</text></view>

        <template v-if="merch.length">
          <view class="pub-stitch" />

          <view class="pub-toc">
            <text class="pub-toc-title">猫协周边</text>
            <view class="pub-toc-leader" />
            <text class="pub-toc-action">纪念品 · 仅展示</text>
          </view>

          <view class="merch-flow">
            <view
              v-for="item in merch"
              :key="item.post_id"
              class="merch-item"
              @tap="goPostDetail(item.post_id)"
            >
              <view class="pub-print">
                <image class="pub-print-img merch-photo" :src="resolvePublicImage(item.cover_url)" mode="aspectFill" />
              </view>
              <text class="merch-name">{{ item.title }}</text>
            </view>
          </view>
        </template>

        <view class="pub-stitch" />

        <!-- About: the association's own words -->
        <view class="pub-toc">
          <text class="pub-toc-title">关于团绒猫协</text>
          <view class="pub-toc-leader" />
        </view>

        <view class="about">
          <text v-for="(para, index) in aboutParagraphs" :key="index" class="about-lead">{{ para }}</text>

          <view v-for="section in introSections" :key="section.title" class="about-sec">
            <text class="about-sec-title">{{ section.title }}</text>
            <text class="about-sec-text">{{ section.text }}</text>
          </view>

          <view v-if="highlightNote" class="about-quote">
            <text>{{ highlightNote }}</text>
          </view>

          <view v-if="feedingTips.length" class="tips">
            <text class="about-sec-title">文明投喂小贴士</text>
            <view v-for="(tip, index) in feedingTips" :key="index" class="tip-row">
              <text class="tip-dot">·</text>
              <text class="tip-text">{{ tip }}</text>
            </view>
          </view>

          <view v-if="site?.join_info" class="about-sec">
            <text class="about-sec-title">如何加入</text>
            <text class="about-sec-text">{{ site.join_info }}</text>
          </view>

          <button v-if="!isLoggedIn" class="pub-btn about-btn" @tap="goLogin">
            我是协会成员，前往登录
          </button>
        </view>

        <view class="pub-footer">
          <text>{{ footerName }} · 用心守护校园的每一只猫</text>
        </view>
        <view class="pub-safe-bottom" />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  getPublicCats,
  getPublicPosts,
  getPublicSiteInfo,
  getPublicStats,
  type PublicCatListItem,
  type PublicPostCard,
  type PublicSiteInfo,
  type PublicStats,
} from "@/api/public";
import { LOGIN_ROUTE, HOME_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import { resolvePublicImage } from "./public-assets";
import { useStatusBarHeight } from "./use-status-bar";

import paperBackground from "../../../素材/加载页素材/背景.jpg";
import catIllustration from "../../../素材/加载页素材/团绒猫.png";
import appWordmark from "../../../素材/加载页素材/团绒喵记本字标.png";

const userStore = useUserStore();
const isLoggedIn = computed(() => userStore.isLoggedIn);
const { statusBarHeight } = useStatusBarHeight();

const site = ref<PublicSiteInfo | null>(null);
const stats = ref<PublicStats | null>(null);
const cats = ref<PublicCatListItem[]>([]);
const trivia = ref<PublicPostCard[]>([]);
const merch = ref<PublicPostCard[]>([]);

const statsLoading = ref(true);
const catsLoading = ref(true);
const triviaLoading = ref(true);

const neuterPercent = computed(() =>
  stats.value ? Math.round(stats.value.neuter_rate * 100) : 0,
);

const heroSubline = computed(() => {
  const university = site.value?.university || "";
  const association = site.value?.association_name || "团绒猫协";
  return university ? `${university} · ${association}` : association;
});

const footerName = computed(() => {
  const association = site.value?.association_name || "团绒猫协";
  const university = site.value?.university || "";
  return university ? `${university}${association}` : association;
});

const aboutParagraphs = computed(() => site.value?.intro_paragraphs ?? []);
const introSections = computed(() => site.value?.intro_sections ?? []);
const highlightNote = computed(() => site.value?.highlight_note ?? "");
const feedingTips = computed(() => site.value?.feeding_tips ?? []);

function padNo(value: number): string {
  return value < 10 ? `0${value}` : `${value}`;
}

function goLogin() {
  uni.reLaunch({ url: LOGIN_ROUTE });
}

function goWorkspace() {
  uni.reLaunch({ url: HOME_ROUTE });
}

function goCats() {
  uni.navigateTo({ url: "/pages/public/cats" });
}

function goCatDetail(catId: string) {
  uni.navigateTo({ url: `/pages/public/cat-detail?cat_id=${encodeURIComponent(catId)}` });
}

function goPostDetail(postId: string) {
  uni.navigateTo({ url: `/pages/public/post-detail?post_id=${encodeURIComponent(postId)}` });
}

async function loadSite() {
  try {
    site.value = await getPublicSiteInfo();
  } catch {
    site.value = null;
  }
}

async function loadStats() {
  statsLoading.value = true;
  try {
    stats.value = await getPublicStats();
  } catch {
    stats.value = null;
  } finally {
    statsLoading.value = false;
  }
}

async function loadCats() {
  catsLoading.value = true;
  try {
    const result = await getPublicCats({ page: 1, page_size: 10 });
    cats.value = result.items;
  } catch {
    cats.value = [];
  } finally {
    catsLoading.value = false;
  }
}

async function loadPosts() {
  triviaLoading.value = true;
  try {
    const [triviaResult, merchResult] = await Promise.all([
      getPublicPosts({ type: "trivia", page: 1, page_size: 3 }),
      getPublicPosts({ type: "merch", page: 1, page_size: 4 }),
    ]);
    trivia.value = triviaResult.items;
    merch.value = merchResult.items;
  } catch {
    trivia.value = [];
    merch.value = [];
  } finally {
    triviaLoading.value = false;
  }
}

onMounted(() => {
  void loadSite();
  void loadStats();
  void loadCats();
  void loadPosts();
});
</script>

<style scoped>
@import "./public-theme.css";

/* ---- hero ---- */

.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 10rpx;
}

.hero-cat {
  width: 220rpx;
  height: 190rpx;
}

.hero-wordmark {
  width: 340rpx;
  height: 82rpx;
  margin-top: 6rpx;
}

.hero-tagline {
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
  color: #5f6d55;
}

.hero-sub {
  margin-top: 10rpx;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: #6d7862;
}

.hero-entry {
  align-self: flex-end;
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx 4rpx;
  font-size: 24rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  color: #267b2f;
  border-bottom: 2rpx solid rgba(38, 123, 47, 0.4);
}

.hero-entry-arrow {
  font-size: 26rpx;
}

/* ---- ledger stats ---- */

.ledger {
  margin-top: 26rpx;
}

.ledger-row {
  display: flex;
  align-items: stretch;
}

.ledger-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}

.ledger-num {
  font-size: 56rpx;
  font-weight: 800;
  line-height: 1.1;
  color: #267b2f;
  font-variant-numeric: tabular-nums;
}

.ledger-unit {
  font-size: 30rpx;
  font-weight: 700;
}

.ledger-label {
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: #78846b;
}

.ledger-rule {
  width: 0;
  border-left: 2rpx dashed rgba(38, 123, 47, 0.3);
  margin: 6rpx 0;
}

.ledger-loading {
  text-align: center;
  font-size: 24rpx;
  color: #6d7862;
  padding: 16rpx 0;
}

/* ---- cats rail ---- */

.rail {
  width: 100%;
  white-space: nowrap;
}

.rail-track {
  display: inline-flex;
  align-items: flex-start;
  gap: 34rpx;
  padding: 20rpx 6rpx 12rpx;
}

.rail-item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  width: 216rpx;
}

.rail-item.tilt-left .rail-print {
  transform: rotate(-1.6deg);
}

.rail-item.tilt-right .rail-print {
  transform: rotate(1.4deg);
}

.rail-print {
  width: 216rpx;
  height: 216rpx;
}

.rail-photo {
  width: 192rpx;
  height: 192rpx;
}

.rail-no {
  margin-top: 10rpx;
  font-size: 20rpx;
  letter-spacing: 2rpx;
  color: #6d7862;
}

.rail-name {
  font-size: 30rpx;
  font-weight: 800;
  color: #31402b;
}

/* ---- trivia rows ---- */

.story-list {
  display: flex;
  flex-direction: column;
}

.story-row {
  display: flex;
  gap: 26rpx;
  padding: 24rpx 0;
  border-bottom: 2rpx solid rgba(49, 64, 43, 0.12);
}

.story-row:last-child {
  border-bottom: 0;
}

.story-print {
  width: 168rpx;
  height: 168rpx;
  flex: 0 0 auto;
}

.story-photo {
  width: 144rpx;
  height: 144rpx;
}

.story-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.story-title {
  font-size: 29rpx;
  font-weight: 800;
  color: #31402b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.story-summary {
  font-size: 23rpx;
  line-height: 1.6;
  color: #78846b;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

/* ---- merch ---- */

.merch-flow {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.merch-item {
  width: 47%;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 30rpx;
}

.merch-photo {
  width: 100%;
  height: 280rpx;
}

.merch-name {
  font-size: 26rpx;
  font-weight: 700;
  color: #31402b;
  line-height: 1.4;
}

/* ---- about ---- */

.about {
  display: flex;
  flex-direction: column;
  gap: 26rpx;
}

.about-lead {
  font-size: 28rpx;
  line-height: 1.85;
  color: #414f39;
}

.about-sec {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.about-sec-title {
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 27rpx;
  font-weight: 800;
  letter-spacing: 3rpx;
  color: #267b2f;
}

.about-sec-title::before {
  content: "";
  width: 20rpx;
  border-top: 4rpx solid rgba(38, 123, 47, 0.55);
}

.about-sec-text {
  font-size: 26rpx;
  line-height: 1.85;
  color: #414f39;
}

.about-quote {
  padding: 6rpx 0 6rpx 26rpx;
  border-left: 4rpx solid rgba(38, 123, 47, 0.5);
  font-size: 26rpx;
  line-height: 1.8;
  color: #3c5c35;
  letter-spacing: 1rpx;
}

.tips {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.tip-row {
  display: flex;
  gap: 12rpx;
}

.tip-dot {
  color: #267b2f;
  font-weight: 800;
}

.tip-text {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6752;
}

.about-btn {
  margin-top: 8rpx;
  width: 100%;
}
</style>
