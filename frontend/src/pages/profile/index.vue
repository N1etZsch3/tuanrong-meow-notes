<template>
  <view class="profile-page">
    <scroll-view class="profile-scroll" scroll-y>
      <view class="page-inner">
        <view class="hero">
          <view class="hero-copy">
            <view class="hero-title-row">
              <text class="hero-title">喵的</text>
              <image class="hero-cat" :src="catLineArt" mode="aspectFit" />
            </view>
            <text class="hero-subtitle">个人信息与任务记录</text>
          </view>
        </view>

        <view class="profile-card" @tap="goProfileDetail">
          <image
            class="avatar"
            :src="avatarDisplay"
            mode="aspectFill"
            @error="avatarLoadFailed = true"
          />
          <view class="profile-main">
            <view class="name-row">
              <text class="nickname">{{ dashboard?.profile.nickname || "未命名成员" }}</text>
              <text class="role-pill" :class="rolePillClass">{{ roleLabel }}</text>
            </view>
            <text class="meta-line">喵喵号 {{ dashboard?.profile.meow_no || "--" }}</text>
            <scroll-view
              v-if="departmentTags.length"
              class="dept-scroll"
              scroll-x
              :show-scrollbar="false"
            >
              <view class="dept-tag-row">
                <text v-for="dept in departmentTags" :key="dept" class="dept-chip">{{ dept }}</text>
              </view>
            </scroll-view>
            <text v-else class="meta-line">部门：未设置</text>
          </view>
          <text class="chevron">›</text>
          <view class="paw-mark" />
        </view>

        <view class="stats-card">
          <button
            v-for="item in PROFILE_STAT_ENTRIES"
            :key="item.key"
            class="stat-button"
            :class="`stat-${item.color}`"
            @tap="goRecord(item.recordType)"
          >
            <view class="stat-icon-shell">
              <image
                v-if="getProfileStatIcon(item)"
                class="stat-icon-image"
                :src="getProfileStatIcon(item)"
                mode="aspectFit"
              />
              <text v-else class="stat-icon-fallback">{{ getProfileStatFallbackIcon(item) }}</text>
            </view>
            <text class="stat-label">{{ item.label }}</text>
            <text class="stat-value">{{ getStatValue(dashboard?.stats || null, item.key) }}</text>
          </button>
        </view>

        <button class="favorite-card" @tap="goRecord('favorite_cats')">
          <view class="favorite-copy">
            <text class="favorite-title">收藏猫咪</text>
            <text class="favorite-subtitle">查看你收藏的猫咪们</text>
            <text class="favorite-action">›</text>
          </view>
          <image class="favorite-image" :src="favoriteCat" mode="aspectFit" />
        </button>

        <view class="menu-card">
          <button class="menu-row" @tap="goAccountSettings">
            <image class="menu-icon-image" :src="profileMenuIconMap.settings" mode="aspectFit" />
            <text class="menu-label">设置</text>
            <text class="menu-chevron">›</text>
          </button>
          <button class="menu-row" @tap="goPublicHome">
            <image class="menu-icon-image" :src="publicHomeIcon" mode="aspectFit" />
            <text class="menu-label">协会公开主页</text>
            <text class="menu-chevron">›</text>
          </button>
        </view>

        <view v-if="isLoading" class="state-line">正在加载个人中心...</view>
        <view v-else-if="errorMessage" class="state-line is-error" @tap="loadDashboard">
          {{ errorMessage }}
        </view>
      </view>
    </scroll-view>
    <AppTabBar active-key="profile" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { onShow } from "@dcloudio/uni-app";

import { resolveUserAvatarContentUrl } from "@/api/files";
import { getMeDashboard, type MeDashboardResponse } from "@/api/me";
import AppTabBar from "@/components/AppTabBar.vue";
import { LOGIN_ROUTE, PUBLIC_HOME_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import {
  PROFILE_STAT_ENTRIES,
  buildRecordRoute,
  getRoleLabel,
  getRolePillClass,
  getStatValue,
  type ProfileRecordType,
} from "./profile-page";
import defaultAvatar from "../../../素材/svg/萌猫/橘猫.svg";
import catLineArt from "../../../素材/svg/萌猫/猫.svg";
import favoriteCat from "../../../素材/svg/萌猫/黑猫.svg";
import taskStatsIcon from "../../../素材/svg/用户页/任务.svg";
import inProgressStatsIcon from "../../../素材/svg/用户页/进行中.svg";
import settingsIcon from "../../../素材/svg/用户页/设置.svg";
import observationIcon from "../../../素材/登录页素材/密码-显示.svg";
import publicHomeIcon from "../../../素材/svg/登录页/猫爪1.svg";

const userStore = useUserStore();
const dashboard = ref<MeDashboardResponse | null>(null);
const isLoading = ref(false);
const errorMessage = ref("");
const PROFILE_DASHBOARD_CACHE_MS = 10_000;
const lastDashboardLoadedAt = ref(0);
const profileStatIconMap: Partial<Record<(typeof PROFILE_STAT_ENTRIES)[number]["key"], string>> = {
  total_completed_tasks: taskStatsIcon,
  monthly_completed_tasks: taskStatsIcon,
  current_in_progress_tasks: inProgressStatsIcon,
  total_observation_records: observationIcon,
};
const profileMenuIconMap = {
  settings: settingsIcon,
} as const;

const avatarLoadFailed = ref(false);
const profileAvatar = computed(
  () =>
    resolveUserAvatarContentUrl(
      dashboard.value?.profile.avatar_url || userStore.currentUser?.avatar_url,
    ) || defaultAvatar,
);
const avatarDisplay = computed(() => (avatarLoadFailed.value ? defaultAvatar : profileAvatar.value));

watch(profileAvatar, () => {
  avatarLoadFailed.value = false;
});
const currentRole = computed(() => dashboard.value?.profile.role || userStore.currentUser?.role);
const roleLabel = computed(() => getRoleLabel(currentRole.value));
const rolePillClass = computed(() => getRolePillClass(currentRole.value));
const departmentTags = computed(() => {
  const list = dashboard.value?.profile.departments;
  if (list && list.length) {
    return list;
  }
  const single = dashboard.value?.profile.department;
  return single ? [single] : [];
});

async function loadDashboard() {
  if (isLoading.value) {
    return;
  }

  if (
    dashboard.value &&
    Date.now() - lastDashboardLoadedAt.value < PROFILE_DASHBOARD_CACHE_MS
  ) {
    return;
  }

  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";
  try {
    dashboard.value = await getMeDashboard(accessToken);
    lastDashboardLoadedAt.value = Date.now();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "个人中心加载失败";
  } finally {
    isLoading.value = false;
  }
}

function goProfileDetail() {
  uni.navigateTo({ url: "/pages/profile/detail" });
}

function goAccountSettings() {
  uni.navigateTo({ url: "/pages/profile/settings" });
}

function goPublicHome() {
  uni.navigateTo({ url: PUBLIC_HOME_ROUTE });
}

function goRecord(type: ProfileRecordType) {
  uni.navigateTo({ url: buildRecordRoute(type) });
}

function getProfileStatIcon(item: (typeof PROFILE_STAT_ENTRIES)[number]) {
  return profileStatIconMap[item.key] || "";
}

function getProfileStatFallbackIcon(item: (typeof PROFILE_STAT_ENTRIES)[number]) {
  return item.icon;
}

onShow(() => {
  void loadDashboard();
});
</script>

<style scoped>
.profile-page {
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 84% 12%, rgba(225, 242, 214, 0.72) 0, rgba(225, 242, 214, 0) 180rpx),
    linear-gradient(180deg, #fbfcfb 0%, #f6faf2 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.profile-scroll {
  height: 100vh;
  box-sizing: border-box;
}

.page-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) 38rpx calc(env(safe-area-inset-bottom) + 164rpx);
}

.hero {
  display: flex;
  align-items: flex-start;
  margin-bottom: 44rpx;
}

.hero-copy {
  min-width: 0;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.hero-title,
.hero-subtitle {
  display: block;
}

.hero-title {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.hero-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.hero-cat {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
  flex: 0 0 auto;
}

.profile-card,
.stats-card,
.favorite-card,
.menu-card {
  box-sizing: border-box;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
}

.profile-card {
  position: relative;
  min-height: 196rpx;
  padding: 34rpx 54rpx 34rpx 34rpx;
  display: flex;
  align-items: center;
  gap: 30rpx;
  overflow: hidden;
}

.avatar {
  width: 132rpx;
  height: 132rpx;
  border: 6rpx solid #ffffff;
  border-radius: 50%;
  background: #edf6e9;
  flex: 0 0 auto;
}

.profile-main {
  position: relative;
  z-index: 1;
  min-width: 0;
  flex: 1;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-width: 0;
}

.nickname {
  overflow: hidden;
  color: #171b22;
  font-size: 36rpx;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-pill {
  border-radius: 12rpx;
  flex: 0 0 auto;
  font-size: 22rpx;
  font-weight: 800;
  padding: 8rpx 14rpx;
}

.role-pill--admin {
  background: #e3f1d6;
  color: #2f8037;
}

.role-pill--member {
  background: #e8f1ff;
  color: #2f68d8;
}

.role-pill--volunteer {
  background: #fff1df;
  color: #df7426;
}

.meta-line {
  display: block;
  margin-top: 14rpx;
  color: #555c67;
  font-size: 25rpx;
  line-height: 1.2;
}

.dept-scroll {
  margin-top: 14rpx;
  width: 100%;
  white-space: nowrap;
}

.dept-tag-row {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
}

.dept-chip {
  flex: 0 0 auto;
  padding: 7rpx 16rpx;
  border-radius: 12rpx;
  background: #e6f6e4;
  color: #238033;
  font-size: 22rpx;
  font-weight: 800;
  line-height: 1.2;
}

.chevron,
.menu-chevron {
  color: #69717d;
  font-size: 58rpx;
  line-height: 1;
}

.paw-mark {
  position: absolute;
  right: -12rpx;
  bottom: -24rpx;
  width: 180rpx;
  height: 122rpx;
  border-radius: 100rpx 100rpx 0 0;
  background: rgba(196, 229, 180, 0.46);
}

.stats-card {
  margin-top: 26rpx;
  padding: 34rpx 14rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat-button {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  line-height: 1;
}

.stat-button::after,
.favorite-card::after,
.menu-row::after {
  border: 0;
}

.stat-button + .stat-button {
  border-left: 2rpx solid #e7ece7;
}

.stat-icon-shell {
  width: 58rpx;
  height: 58rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-image {
  width: 54rpx;
  height: 54rpx;
}

.stat-icon-fallback {
  width: 54rpx;
  height: 54rpx;
  border-radius: 16rpx;
  background: #8056df;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 54rpx;
  text-align: center;
}

.stat-green .stat-icon-image {
  filter: brightness(0) saturate(100%) invert(33%) sepia(65%) saturate(1011%) hue-rotate(84deg) brightness(93%) contrast(91%);
}

.stat-blue .stat-icon-image {
  filter: brightness(0) saturate(100%) invert(52%) sepia(92%) saturate(2389%) hue-rotate(199deg) brightness(98%) contrast(94%);
}

.stat-orange .stat-icon-image {
  filter: brightness(0) saturate(100%) invert(60%) sepia(87%) saturate(1903%) hue-rotate(347deg) brightness(99%) contrast(93%);
}

.stat-purple .stat-icon-image {
  filter: brightness(0) saturate(100%) invert(42%) sepia(80%) saturate(2012%) hue-rotate(236deg) brightness(95%) contrast(91%);
}

.stat-label {
  color: #4d535d;
  font-size: 24rpx;
}

.stat-value {
  color: currentColor;
  font-size: 40rpx;
  font-weight: 900;
}

.stat-green {
  color: #278331;
}

.stat-blue {
  color: #4a85f4;
}

.stat-orange {
  color: #f47b24;
}

.stat-purple {
  color: #8056df;
}

.favorite-card {
  width: 100%;
  min-height: 180rpx;
  margin: 28rpx 0 0;
  padding: 26rpx 34rpx;
  border: 2rpx solid rgba(226, 241, 218, 0.95);
  background: linear-gradient(100deg, #f8fff2 0%, #ffffff 52%, #eef9e6 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.favorite-copy {
  min-width: 0;
}

.favorite-title,
.favorite-subtitle,
.favorite-action {
  display: block;
}

.favorite-title {
  color: #1c2026;
  font-size: 34rpx;
  font-weight: 900;
}

.favorite-subtitle {
  margin-top: 14rpx;
  color: #626a75;
  font-size: 25rpx;
}

.favorite-action {
  width: 54rpx;
  height: 54rpx;
  margin-top: 24rpx;
  border-radius: 50%;
  background: #6caf55;
  color: #ffffff;
  font-size: 52rpx;
  line-height: 44rpx;
  text-align: center;
}

.favorite-image {
  width: 232rpx;
  height: 150rpx;
  flex: 0 0 auto;
}

.menu-card {
  margin-top: 28rpx;
  padding: 16rpx 26rpx;
}

.menu-row {
  height: 100rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #2c3036;
  display: flex;
  align-items: center;
  text-align: left;
}

.menu-row + .menu-row {
  border-top: 2rpx solid #eef1ef;
}

.menu-icon-image,
.menu-icon-fallback {
  width: 68rpx;
  height: 42rpx;
  flex: 0 0 68rpx;
}

.menu-icon-image {
  filter: brightness(0) saturate(100%) invert(36%) sepia(33%) saturate(1009%) hue-rotate(75deg) brightness(92%) contrast(91%);
}

.menu-icon-fallback {
  color: #2f8037;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 42rpx;
}

.menu-label {
  flex: 1;
  color: #2c3036;
  font-size: 28rpx;
}

.menu-chevron {
  font-size: 46rpx;
}

.state-line {
  margin-top: 22rpx;
  color: #767d85;
  font-size: 24rpx;
  text-align: center;
}

.state-line.is-error {
  color: #c34839;
}
</style>
