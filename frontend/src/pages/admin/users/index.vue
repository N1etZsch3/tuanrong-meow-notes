<template>
  <view class="members-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="members-inner">
      <view class="nav-row">
        <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
        <view>
          <text class="nav-title">人员管理</text>
          <text class="nav-subtitle">查看、筛选和维护猫协成员资料</text>
        </view>
      </view>

      <view class="fixed-tools">
        <view class="search-box">
          <text class="search-icon">⌕</text>
          <input
            v-model.trim="keyword"
            class="search-input"
            confirm-type="search"
            placeholder="搜索昵称 / 喵喵号 / 姓名"
            placeholder-class="search-placeholder"
            @confirm="reloadUsers"
          />
          <button class="search-button" hover-class="button-hover" @tap="reloadUsers">
            搜索
          </button>
        </view>

        <view class="filter-card">
          <picker
            class="filter-picker"
            :range="roleOptions"
            range-key="label"
            :value="selectedRoleIndex"
            @change="selectRole"
          >
            <view class="filter-control">
              <text class="picker-caption">身份</text>
              <text class="picker-value">{{ selectedRoleLabel }}</text>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="departmentOptions"
            range-key="label"
            :value="selectedDepartmentIndex"
            @change="selectDepartment"
          >
            <view class="filter-control">
              <text class="picker-caption">部门</text>
              <text class="picker-value">{{ selectedDepartmentLabel }}</text>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="sortOptions"
            range-key="label"
            :value="selectedSortIndex"
            @change="selectSort"
          >
            <view class="filter-control">
              <text class="picker-caption">排序</text>
              <text class="picker-value">{{ selectedSortLabel }}</text>
            </view>
          </picker>
        </view>
      </view>

      <scroll-view
        class="member-scroll"
        scroll-y
        enhanced
        lower-threshold="140"
        :show-scrollbar="false"
        @scrolltolower="loadMoreUsers"
      >
        <view v-if="loadState === 'loading' && users.length === 0" class="state-card">
          <text>正在加载成员列表...</text>
        </view>
        <view v-else-if="loadState === 'error' && users.length === 0" class="state-card is-error">
          <text>{{ errorMessage || "成员列表加载失败" }}</text>
        </view>
        <view v-else-if="users.length === 0" class="state-card">
          <text>暂无符合条件的成员</text>
        </view>

        <view v-else class="member-list">
          <view
            v-for="user in users"
            :key="user.id"
            class="member-card"
            hover-class="member-card-hover"
            @tap="goUserDetail(user.id)"
          >
            <IdentityAvatar
              :src="memberAvatar(user)"
              :role="user.role"
              size="list"
              @error="markAvatarFailed(user.id)"
            />
            <view class="member-main">
              <TitleIdentityName
                :name="user.profile.nickname"
                :title="user.profile.title"
                size="list"
              />
              <text class="member-no">{{ user.meow_no }}</text>
            </view>
            <view
              class="department-panel"
              :class="{ 'is-single': memberDepartments(user).length === 1 }"
            >
              <swiper
                v-if="memberDepartmentPages(user).length > 1"
                class="department-swiper"
                vertical
                :duration="220"
                @touchstart.stop="stopDepartmentGesture"
                @touchmove.stop="stopDepartmentGesture"
                @touchend.stop="stopDepartmentGesture"
                @touchcancel.stop="stopDepartmentGesture"
                @tap.stop="stopDepartmentGesture"
              >
                <swiper-item
                  v-for="(page, pageIndex) in memberDepartmentPages(user)"
                  :key="`${user.id}-departments-${pageIndex}`"
                >
                  <view class="department-stack">
                    <text
                      v-for="dept in page"
                      :key="dept"
                      class="department-tag"
                      :style="getDepartmentTagStyle(dept)"
                    >{{ dept }}</text>
                  </view>
                </swiper-item>
              </swiper>
              <view v-else class="department-stack">
                <template v-for="page in memberDepartmentPages(user)" :key="page.join('|')">
                  <text
                    v-for="dept in page"
                    :key="dept"
                    class="department-tag"
                    :style="getDepartmentTagStyle(dept)"
                  >{{ dept }}</text>
                </template>
              </view>
            </view>
            <text class="card-arrow">›</text>
          </view>
          <view class="list-footer">
            <text v-if="isLoadingMore">正在加载更多成员...</text>
            <text v-else-if="!hasMore">已展示全部 {{ total }} 位成员</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <button class="floating-add" hover-class="button-hover" @tap="goCreateUser">
      新增成员
    </button>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import { listAdminUsers, type AdminUserDto } from "@/api/admin-users";
import { resolveUserAvatarContentUrl } from "@/api/files";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import { DEPARTMENTS, getDepartmentTagStyle } from "@/constants/departments";
import IdentityAvatar from "@/components/IdentityAvatar.vue";
import TitleIdentityName from "@/components/TitleIdentityName.vue";

import defaultAvatar from "../../../../素材/svg/萌猫/橘猫.svg";
import loadingBackground from "../../../../素材/加载页素材/背景.jpg";

type PickerChangeEvent = { detail: { value: string | number } };

const PAGE_SIZE = 10;
const roleOptions = [
  { label: "全部", value: "" },
  { label: "超级管理员", value: "super_admin" },
  { label: "管理员", value: "admin" },
  { label: "成员", value: "member" },
  { label: "暑期志愿者", value: "summer_volunteer" },
];
const departmentOptions = [
  { label: "全部", value: "" },
  ...DEPARTMENTS.map((department) => ({ label: department, value: department })),
];
const sortOptions = [
  { label: "喵喵号正序", value: "asc" },
  { label: "喵喵号倒序", value: "desc" },
];

const userStore = useUserStore();
const users = ref<AdminUserDto[]>([]);
const keyword = ref("");
const selectedRole = ref("");
const selectedDepartment = ref("");
const selectedSort = ref<"asc" | "desc">("asc");
const page = ref(1);
const total = ref(0);
const hasMore = ref(false);
const loadState = ref<"idle" | "loading" | "ready" | "error">("idle");
const isLoadingMore = ref(false);
const errorMessage = ref("");
const failedAvatarUserIds = ref<Set<string>>(new Set());

function memberAvatar(user: AdminUserDto): string {
  const avatarUrl = user.profile.avatar_url;
  if (!avatarUrl || failedAvatarUserIds.value.has(user.id)) {
    return defaultAvatar;
  }
  return resolveUserAvatarContentUrl(avatarUrl) || defaultAvatar;
}

function markAvatarFailed(id: string) {
  failedAvatarUserIds.value = new Set(failedAvatarUserIds.value).add(id);
}

function memberDepartments(user: AdminUserDto): string[] {
  if (user.profile.departments?.length) {
    return user.profile.departments;
  }
  return [user.profile.department || "未分部"];
}

function memberDepartmentPages(user: AdminUserDto): string[][] {
  const departments = memberDepartments(user);
  const pages: string[][] = [];
  for (let index = 0; index < departments.length; index += 2) {
    pages.push(departments.slice(index, index + 2));
  }
  return pages;
}

function stopDepartmentGesture() {
  // 阻止纵向 swiper 的触摸事件冒泡到外层人员列表，保留 swiper 自身默认翻页。
}

const selectedRoleIndex = computed(() =>
  Math.max(0, roleOptions.findIndex((item) => item.value === selectedRole.value)),
);
const selectedDepartmentIndex = computed(() =>
  Math.max(0, departmentOptions.findIndex((item) => item.value === selectedDepartment.value)),
);
const selectedSortIndex = computed(() =>
  Math.max(0, sortOptions.findIndex((item) => item.value === selectedSort.value)),
);
const selectedRoleLabel = computed(() => roleOptions[selectedRoleIndex.value]?.label || "全部");
const selectedDepartmentLabel = computed(
  () => departmentOptions[selectedDepartmentIndex.value]?.label || "全部",
);
const selectedSortLabel = computed(
  () => sortOptions[selectedSortIndex.value]?.label || "喵喵号正序",
);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return null;
  }
  return accessToken;
}

async function loadUsers(options: { reset?: boolean } = { reset: true }) {
  const reset = options.reset ?? true;
  if (!reset && (isLoadingMore.value || !hasMore.value)) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  const nextPage = reset ? 1 : page.value + 1;
  if (reset) {
    loadState.value = "loading";
  } else {
    isLoadingMore.value = true;
  }
  try {
    const response = await listAdminUsers(token, {
      page: nextPage,
      page_size: PAGE_SIZE,
      keyword: keyword.value,
      role: selectedRole.value,
      department: selectedDepartment.value,
      sort_by: "meow_no",
      sort_order: selectedSort.value,
    });
    users.value = reset ? response.items : [...users.value, ...response.items];
    page.value = response.page;
    total.value = response.total;
    hasMore.value = response.has_more;
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value = error instanceof Error ? error.message : "成员列表加载失败";
  } finally {
    isLoadingMore.value = false;
  }
}

function reloadUsers() {
  void loadUsers({ reset: true });
}

function loadMoreUsers() {
  void loadUsers({ reset: false });
}

function pickerIndex(event: PickerChangeEvent) {
  return Number(event.detail.value) || 0;
}

function selectRole(event: PickerChangeEvent) {
  selectedRole.value = roleOptions[pickerIndex(event)]?.value || "";
  reloadUsers();
}

function selectDepartment(event: PickerChangeEvent) {
  selectedDepartment.value = departmentOptions[pickerIndex(event)]?.value || "";
  reloadUsers();
}

function selectSort(event: PickerChangeEvent) {
  selectedSort.value = (sortOptions[pickerIndex(event)]?.value || "asc") as "asc" | "desc";
  reloadUsers();
}

function goUserDetail(userId: string) {
  uni.navigateTo({ url: `/pages/admin/users/detail?user_id=${userId}` });
}

function goCreateUser() {
  uni.navigateTo({ url: "/pages/admin/create-user" });
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  reloadUsers();
});
</script>

<style scoped>
.members-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #111827;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.members-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 42rpx);
  display: flex;
  flex-direction: column;
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
  flex: 0 0 auto;
}

.back-button,
.search-button,
.member-card,
.floating-add {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.search-button::after,
.member-card::after,
.floating-add::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.member-no {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.fixed-tools {
  flex: 0 0 auto;
  margin-top: 30rpx;
}

.search-box,
.filter-card,
.member-card,
.state-card {
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.search-box {
  height: 76rpx;
  border-radius: 24rpx;
  padding: 0 14rpx 0 24rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.search-icon {
  color: #323946;
  font-size: 36rpx;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 76rpx;
  color: #222831;
  font-size: 25rpx;
}

.search-placeholder {
  color: #969da8;
}

.search-button {
  width: 84rpx;
  height: 50rpx;
  border-radius: 16rpx;
  background: #2f8a38;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 50rpx;
}

.filter-card {
  margin-top: 20rpx;
  border-radius: 26rpx;
  padding: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.picker-caption,
.picker-value {
  display: block;
}

.picker-caption {
  color: rgba(82, 90, 102, 0.68);
  font-size: 19rpx;
  font-weight: 800;
}

.picker-value {
  box-sizing: border-box;
  height: 58rpx;
  margin-top: 10rpx;
  border: 2rpx solid #c4dac2;
  border-radius: 19rpx;
  padding: 0 14rpx;
  overflow: hidden;
  color: #151a20;
  font-size: 21rpx;
  font-weight: 900;
  line-height: 54rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 24rpx;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding-bottom: 130rpx;
}

.member-card {
  position: relative;
  box-sizing: border-box;
  height: 168rpx;
  border-radius: 26rpx;
  padding: 22rpx 58rpx 22rpx 22rpx;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 22rpx;
  text-align: left;
}

.member-card-hover,
.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.member-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  flex: 1;
}

.member-no {
  margin-top: 7rpx;
  color: #6b7280;
  font-size: 25rpx;
  font-weight: 800;
}

.department-panel {
  width: 156rpx;
  height: 84rpx;
  flex: 0 0 auto;
}

.department-swiper {
  width: 100%;
  height: 84rpx;
}

.department-stack {
  min-height: 84rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.department-tag {
  box-sizing: border-box;
  max-width: 156rpx;
  border-radius: 15rpx;
  padding: 6rpx 13rpx;
  overflow: hidden;
  font-size: 21rpx;
  font-weight: 900;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.department-panel.is-single .department-stack {
  justify-content: center;
}

.card-arrow {
  position: absolute;
  right: 22rpx;
  top: 50%;
  color: #6b7280;
  font-size: 52rpx;
  transform: translateY(-50%);
}

.state-card {
  border-radius: 26rpx;
  padding: 42rpx 30rpx;
  color: #4c555f;
  font-size: 28rpx;
  font-weight: 900;
  text-align: center;
}

.state-card.is-error {
  color: #c34839;
}

.list-footer {
  min-height: 58rpx;
  color: #6a7480;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 58rpx;
  text-align: center;
}

.floating-add {
  position: fixed;
  z-index: 5;
  right: 34rpx;
  bottom: calc(env(safe-area-inset-bottom) + 34rpx);
  width: 168rpx;
  height: 78rpx;
  border-radius: 999rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}
</style>
