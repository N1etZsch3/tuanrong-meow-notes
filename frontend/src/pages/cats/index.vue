<template>
  <view class="cats-page">
    <scroll-view class="cats-scroll" scroll-y refresher-enabled :refresher-triggered="isRefreshing" @refresherrefresh="refreshPage">
      <view class="page-inner">
        <view class="hero">
          <view class="hero-icon-shell">
            <image class="hero-icon" :src="catIcon" mode="aspectFit" />
          </view>
          <view class="hero-copy">
            <text class="hero-title">猫咪库</text>
            <text class="hero-subtitle">校园猫咪档案管理</text>
          </view>
        </view>

        <view class="stats-card">
          <view v-for="item in statsItems" :key="item.key" class="stat-item" :class="`stat-${item.tone}`">
            <text class="stat-label">{{ item.label }}</text>
            <text class="stat-value">{{ item.value }}</text>
          </view>
          <view class="neuter-rate">
            <text class="rate-label">绝育率</text>
            <text class="rate-value">{{ resolvedStats.neuter_rate }}%</text>
          </view>
        </view>

        <view class="search-box">
          <text class="search-icon">⌕</text>
          <input
            v-model="keyword"
            class="search-input"
            confirm-type="search"
            placeholder="搜索猫名 / 别名 / 花色 / 区域"
            placeholder-class="search-placeholder"
            @confirm="handleSearchConfirm"
          />
          <button class="search-button" @tap="handleSearchConfirm">搜索</button>
        </view>

        <view class="filter-card">
          <picker
            class="filter-picker"
            :range="filterKeyPickerOptions"
            range-key="label"
            :value="selectedFilterKeyIndex"
            @change="handleFilterKeyChange"
          >
            <view class="picker-shell">
              <text class="picker-caption">筛选项</text>
              <text class="picker-value">{{ selectedFilterKeyLabel }}</text>
              <text class="picker-arrow">⌄</text>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="filterValuePickerOptions"
            range-key="label"
            :value="selectedFilterValueIndex"
            @change="handleFilterValueChange"
          >
            <view class="picker-shell">
              <text class="picker-caption">可选值</text>
              <text class="picker-value">{{ selectedFilterValueLabel }}</text>
              <text class="picker-arrow">⌄</text>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="sortOptions"
            range-key="label"
            :value="selectedSortIndex"
            @change="handleSortChange"
          >
            <view class="picker-shell">
              <text class="picker-caption">排序</text>
              <text class="picker-value">{{ selectedSortLabel }}</text>
              <text class="picker-arrow">⌄</text>
            </view>
          </picker>
          <button class="clear-filter-button" @tap="clearFilters">
            <text class="clear-icon">⌫</text>
            <text>清除筛选</text>
          </button>
        </view>

        <view v-if="isLoading" class="state-panel">
          <text class="state-title">正在加载猫咪档案...</text>
        </view>
        <view v-else-if="errorMessage" class="state-panel is-error" @tap="loadCatsPage">
          <text class="state-title">{{ errorMessage }}</text>
          <text class="state-action">点按重试</text>
        </view>
        <view v-else-if="cats.length === 0" class="state-panel empty-list">
          <text class="state-title">暂无猫咪档案</text>
          <text class="state-desc">当前筛选下没有可展示的猫咪记录</text>
        </view>

        <view v-else class="cat-list">
          <button
            v-for="cat in cats"
            :key="cat.cat_id"
            class="cat-card"
            hover-class="cat-card-hover"
            @tap="goCatDetail(cat.cat_id)"
          >
            <image
              v-if="shouldShowImage(cat)"
              class="cat-photo"
              :src="cat.avatar_thumbnail_url || cat.avatar_url || ''"
              mode="aspectFill"
              @error="markImageFailed(cat.cat_id)"
            />
            <view v-else class="cat-photo-placeholder">
              <text>暂无照片</text>
            </view>
            <view class="cat-main">
              <view class="cat-name-row">
                <text class="cat-name">{{ cat.name }}</text>
                <text v-if="cat.is_favorited" class="favorite-mark">已收藏</text>
              </view>
              <text class="cat-meta">{{ cat.coat_color }}{{ cat.alias_summary ? ` · 别名${cat.alias_summary}` : "" }}</text>
              <view class="cat-line">
                <text class="line-icon">⌖</text>
                <text class="line-text">{{ cat.resident_area_text }}</text>
              </view>
              <view class="cat-line">
                <text class="line-icon">◷</text>
                <text class="line-text">{{ formatCatSeenTime(cat.last_seen_at) }}</text>
              </view>
            </view>
            <view class="tag-column">
              <text
                v-for="tag in cat.display_tags"
                :key="`${cat.cat_id}-${tag}`"
                class="cat-tag"
                :class="`tag-${getCatTagTone(tag)}`"
              >
                {{ tag }}
              </text>
            </view>
            <text class="card-arrow">›</text>
          </button>
        </view>
      </view>
    </scroll-view>
    <AppTabBar active-key="cats" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import {
  getCatFilterOptions,
  getCatStats,
  getCats,
  type CatFilterOption,
  type CatListItemDto,
  type CatSortOption,
  type CatStatsResponse,
} from "@/api/cats";
import AppTabBar from "@/components/AppTabBar.vue";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import {
  buildCatListQuery,
  formatCatSeenTime,
  getCatTagTone,
  normalizeCatStats,
} from "./cats-page";
import catIcon from "../../../素材/icon/猫咪.png";

type PickerChangeEvent = {
  detail: {
    value: string | number;
  };
};

const PAGE_SIZE = 20;
const DEFAULT_SORT_OPTION: CatSortOption = { value: "last_seen_desc", label: "最近出现" };

const userStore = useUserStore();
const stats = ref<CatStatsResponse | null>(null);
const filterOptions = ref<CatFilterOption[]>([]);
const sortOptions = ref<CatSortOption[]>([DEFAULT_SORT_OPTION]);
const cats = ref<CatListItemDto[]>([]);
const keyword = ref("");
const selectedFilterKey = ref("");
const selectedFilterValue = ref("");
const selectedSort = ref(DEFAULT_SORT_OPTION.value);
const isLoading = ref(false);
const isRefreshing = ref(false);
const errorMessage = ref("");
const imageFailedIds = ref<string[]>([]);

const resolvedStats = computed(() => normalizeCatStats(stats.value));
const statsItems = computed(() => [
  { key: "total", label: "在档猫咪", value: resolvedStats.value.total_cats, tone: "green" },
  { key: "active", label: "正常在校", value: resolvedStats.value.active_cats, tone: "green" },
  { key: "adoption", label: "待领养", value: resolvedStats.value.waiting_adoption_cats, tone: "orange" },
  { key: "watching", label: "待观察", value: resolvedStats.value.watching_cats, tone: "blue" },
  { key: "neutered", label: "已绝育", value: resolvedStats.value.neutered_cats, tone: "purple" },
]);

const filterKeyPickerOptions = computed(() => [
  { key: "", label: "筛选项", values: [] },
  ...filterOptions.value,
]);
const selectedFilterOption = computed(() =>
  filterOptions.value.find((item) => item.key === selectedFilterKey.value) ?? null,
);
const filterValuePickerOptions = computed(() => [
  { value: "", label: "全部" },
  ...(selectedFilterOption.value?.values ?? []),
]);
const selectedFilterKeyIndex = computed(() =>
  Math.max(0, filterKeyPickerOptions.value.findIndex((item) => item.key === selectedFilterKey.value)),
);
const selectedFilterValueIndex = computed(() =>
  Math.max(0, filterValuePickerOptions.value.findIndex((item) => item.value === selectedFilterValue.value)),
);
const selectedSortIndex = computed(() =>
  Math.max(0, sortOptions.value.findIndex((item) => item.value === selectedSort.value)),
);
const selectedFilterKeyLabel = computed(
  () => filterKeyPickerOptions.value[selectedFilterKeyIndex.value]?.label ?? "筛选项",
);
const selectedFilterValueLabel = computed(
  () => filterValuePickerOptions.value[selectedFilterValueIndex.value]?.label ?? "全部",
);
const selectedSortLabel = computed(
  () => sortOptions.value[selectedSortIndex.value]?.label ?? DEFAULT_SORT_OPTION.label,
);

async function resolveAccessToken() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return null;
  }
  return accessToken;
}

async function loadCatsList(accessToken?: string) {
  const token = accessToken ?? await resolveAccessToken();
  if (!token) {
    return;
  }
  const response = await getCats(
    token,
    buildCatListQuery({
      keyword: keyword.value,
      filter_key: selectedFilterKey.value,
      filter_value: selectedFilterValue.value,
      sort: selectedSort.value,
      page: 1,
      page_size: PAGE_SIZE,
    }),
  );
  cats.value = response.items;
}

async function loadCatsPage() {
  const accessToken = await resolveAccessToken();
  if (!accessToken) {
    return;
  }
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const [statsResponse, optionsResponse, listResponse] = await Promise.all([
      getCatStats(accessToken),
      getCatFilterOptions(accessToken),
      getCats(
        accessToken,
        buildCatListQuery({
          keyword: keyword.value,
          filter_key: selectedFilterKey.value,
          filter_value: selectedFilterValue.value,
          sort: selectedSort.value,
          page: 1,
          page_size: PAGE_SIZE,
        }),
      ),
    ]);
    stats.value = statsResponse;
    filterOptions.value = optionsResponse.filter_options;
    sortOptions.value = optionsResponse.sort_options.length > 0 ? optionsResponse.sort_options : [DEFAULT_SORT_OPTION];
    cats.value = listResponse.items;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "猫咪库加载失败";
  } finally {
    isLoading.value = false;
    isRefreshing.value = false;
  }
}

async function refreshPage() {
  isRefreshing.value = true;
  await loadCatsPage();
}

async function handleSearchConfirm() {
  errorMessage.value = "";
  try {
    await loadCatsList();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "猫咪列表刷新失败";
  }
}

function pickerIndex(event: PickerChangeEvent) {
  return Number(event.detail.value) || 0;
}

function handleFilterKeyChange(event: PickerChangeEvent) {
  const selected = filterKeyPickerOptions.value[pickerIndex(event)];
  selectedFilterKey.value = selected?.key ?? "";
  selectedFilterValue.value = "";
  void handleSearchConfirm();
}

function handleFilterValueChange(event: PickerChangeEvent) {
  const selected = filterValuePickerOptions.value[pickerIndex(event)];
  selectedFilterValue.value = selected?.value ?? "";
  void handleSearchConfirm();
}

function handleSortChange(event: PickerChangeEvent) {
  const selected = sortOptions.value[pickerIndex(event)];
  selectedSort.value = selected?.value ?? DEFAULT_SORT_OPTION.value;
  void handleSearchConfirm();
}

function clearFilters() {
  keyword.value = "";
  selectedFilterKey.value = "";
  selectedFilterValue.value = "";
  selectedSort.value = DEFAULT_SORT_OPTION.value;
  void handleSearchConfirm();
}

function markImageFailed(catId: string) {
  if (!imageFailedIds.value.includes(catId)) {
    imageFailedIds.value = [...imageFailedIds.value, catId];
  }
}

function shouldShowImage(cat: CatListItemDto) {
  return Boolean((cat.avatar_thumbnail_url || cat.avatar_url) && !imageFailedIds.value.includes(cat.cat_id));
}

function goCatDetail(catId: string) {
  uni.navigateTo({ url: `/pages/cats/detail?id=${catId}` });
}

onShow(() => {
  void loadCatsPage();
});
</script>

<style scoped>
.cats-page {
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 84% 10%, rgba(210, 237, 195, 0.72) 0, rgba(210, 237, 195, 0) 190rpx),
    linear-gradient(180deg, #fbfdf8 0%, #f5faf1 100%);
  color: #151a20;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.cats-scroll {
  height: 100vh;
  box-sizing: border-box;
}

.page-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: 72rpx 32rpx calc(env(safe-area-inset-bottom) + 154rpx);
}

.hero {
  display: flex;
  align-items: center;
  gap: 24rpx;
  margin-bottom: 34rpx;
}

.hero-icon-shell {
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 34rpx rgba(48, 101, 50, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-icon {
  width: 54rpx;
  height: 54rpx;
}

.hero-copy {
  min-width: 0;
}

.hero-title,
.hero-subtitle {
  display: block;
}

.hero-title {
  color: #111720;
  font-size: 54rpx;
  font-weight: 900;
  line-height: 1.1;
}

.hero-subtitle {
  margin-top: 12rpx;
  color: #68707b;
  font-size: 27rpx;
  line-height: 1.2;
}

.stats-card,
.search-box,
.filter-card,
.cat-card,
.state-panel {
  box-sizing: border-box;
  border: 2rpx solid rgba(223, 237, 216, 0.9);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
}

.stats-card {
  border-radius: 30rpx;
  padding: 30rpx 22rpx 24rpx;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  row-gap: 26rpx;
}

.stat-item {
  min-width: 0;
  text-align: center;
}

.stat-item + .stat-item {
  border-left: 2rpx solid #e4eee0;
}

.stat-label,
.stat-value {
  display: block;
}

.stat-label {
  color: #2d333b;
  font-size: 23rpx;
  line-height: 1.1;
}

.stat-value {
  margin-top: 15rpx;
  font-size: 48rpx;
  font-weight: 900;
  line-height: 1;
}

.stat-green .stat-value {
  color: #228031;
}

.stat-blue .stat-value {
  color: #3389e6;
}

.stat-orange .stat-value {
  color: #ee7c18;
}

.stat-purple .stat-value {
  color: #785fe8;
}

.neuter-rate {
  grid-column: 1 / -1;
  border-top: 2rpx dashed #dcebd5;
  padding-top: 22rpx;
  color: #17202a;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
  font-size: 29rpx;
  font-weight: 900;
}

.rate-value {
  color: #238033;
  font-size: 38rpx;
}

.search-box {
  min-height: 88rpx;
  margin-top: 28rpx;
  border: 0;
  border-radius: 28rpx;
  padding: 0 16rpx 0 28rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.search-icon {
  color: #323946;
  font-size: 42rpx;
  line-height: 1;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 88rpx;
  color: #222831;
  font-size: 28rpx;
}

.search-placeholder {
  color: #969da8;
}

.search-button,
.clear-filter-button,
.cat-card {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
}

.search-button::after,
.clear-filter-button::after,
.cat-card::after {
  border: 0;
}

.search-button {
  width: 96rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #2f8a38;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.filter-card {
  margin-top: 28rpx;
  border-radius: 28rpx;
  padding: 24rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx;
}

.filter-picker {
  min-width: 0;
}

.picker-shell {
  height: 76rpx;
  box-sizing: border-box;
  border: 2rpx solid #cfe4c9;
  border-radius: 24rpx;
  padding: 8rpx 18rpx;
  background: rgba(255, 255, 255, 0.78);
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.picker-caption,
.picker-value,
.picker-arrow {
  line-height: 1;
}

.picker-caption {
  display: none;
}

.picker-value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #20262e;
  font-size: 25rpx;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow {
  color: #151a20;
  font-size: 30rpx;
}

.clear-filter-button {
  grid-column: 1 / -1;
  height: 62rpx;
  color: #278435;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 62rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.clear-icon {
  font-size: 30rpx;
}

.state-panel {
  margin-top: 28rpx;
  border-radius: 28rpx;
  padding: 44rpx 30rpx;
  text-align: center;
}

.state-title,
.state-desc,
.state-action {
  display: block;
}

.state-title {
  color: #4c555f;
  font-size: 29rpx;
  font-weight: 900;
}

.state-desc {
  margin-top: 14rpx;
  color: #7a838e;
  font-size: 25rpx;
}

.state-action {
  margin-top: 14rpx;
  color: #2c8136;
  font-size: 24rpx;
  font-weight: 900;
}

.state-panel.is-error .state-title {
  color: #c34839;
}

.cat-list {
  margin-top: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.cat-card {
  position: relative;
  min-height: 178rpx;
  border-radius: 28rpx;
  padding: 24rpx 54rpx 24rpx 22rpx;
  color: #151a20;
  display: flex;
  align-items: center;
  gap: 24rpx;
  text-align: left;
}

.cat-card-hover {
  transform: translateY(2rpx);
  opacity: 0.94;
}

.cat-photo,
.cat-photo-placeholder {
  width: 132rpx;
  height: 132rpx;
  border-radius: 18rpx;
  flex: 0 0 auto;
}

.cat-photo-placeholder {
  background: linear-gradient(135deg, #e8f4e0 0%, #f9fbf7 100%);
  color: #6c8a62;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 900;
}

.cat-main {
  min-width: 0;
  flex: 1;
}

.cat-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.cat-name {
  min-width: 0;
  overflow: hidden;
  color: #121820;
  font-size: 36rpx;
  font-weight: 900;
  line-height: 1.18;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.favorite-mark {
  border-radius: 12rpx;
  background: #fff3d8;
  color: #b36a00;
  flex: 0 0 auto;
  font-size: 20rpx;
  font-weight: 900;
  padding: 7rpx 10rpx;
}

.cat-meta,
.cat-line {
  color: #535d69;
  font-size: 24rpx;
  line-height: 1.25;
}

.cat-meta {
  display: block;
  margin-top: 14rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-line {
  margin-top: 10rpx;
  display: flex;
  align-items: center;
  gap: 9rpx;
}

.line-icon {
  width: 24rpx;
  color: #3d4651;
  font-size: 24rpx;
}

.line-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-column {
  width: 148rpx;
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10rpx;
}

.cat-tag {
  max-width: 140rpx;
  border-radius: 14rpx;
  padding: 8rpx 13rpx;
  overflow: hidden;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-green {
  background: #e7f6df;
  color: #238033;
}

.tag-blue {
  background: #e6f0ff;
  color: #2d72d9;
}

.tag-orange {
  background: #fff0e2;
  color: #e46c14;
}

.tag-red {
  background: #ffe7eb;
  color: #d73546;
}

.tag-purple {
  background: #eee8ff;
  color: #684ce5;
}

.tag-gray {
  background: #edf1ef;
  color: #57616b;
}

.card-arrow {
  position: absolute;
  right: 22rpx;
  top: 50%;
  color: #15922d;
  font-size: 56rpx;
  line-height: 1;
  transform: translateY(-50%);
}
</style>
