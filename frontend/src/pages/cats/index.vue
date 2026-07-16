<template>
  <view class="cats-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />

    <view class="cats-inner">
      <view class="cats-fixed">
        <view class="page-title">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view class="title-copy">
            <view class="page-title-row">
              <text class="page-title-text">猫咪库</text>
              <image class="page-title-icon" :src="titleMascotIcon" mode="aspectFit" />
            </view>
            <text class="page-title-subtitle">记录校园里的每一位喵校友</text>
          </view>
        </view>

        <view class="stats-card">
          <view class="stats-grid">
            <view v-for="item in statsItems" :key="item.key" class="stat-item">
              <image
                v-if="item.has_icon !== false"
                class="stat-icon"
                :class="`stat-icon-${item.tone}`"
                :src="statIconMap[item.key]"
                mode="aspectFit"
              />
              <view v-else class="stat-icon-placeholder" />
              <text class="stat-label">{{ item.label }}</text>
              <text class="stat-value" :class="`stat-value-${item.tone}`">{{ item.value }}</text>
            </view>
          </view>
          <view class="neuter-rate-row">
            <text>当前已绝育</text>
            <text class="neuter-count">{{ resolvedStats.neutered_cats }}</text>
            <text>只流浪喵</text>
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
            @tap="openPicker('filter_key')"
            @cancel="closePicker"
            @change="handleFilterKeyChange"
          >
            <view class="filter-control">
              <text class="picker-caption">筛选项</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedFilterKeyLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'filter_key' }"
                  :src="filterArrowIcon"
                  mode="aspectFit"
                />
              </view>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="filterValuePickerOptions"
            range-key="label"
            :value="selectedFilterValueIndex"
            @tap="openPicker('filter_value')"
            @cancel="closePicker"
            @change="handleFilterValueChange"
          >
            <view class="filter-control">
              <text class="picker-caption">可选值</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedFilterValueLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'filter_value' }"
                  :src="filterArrowIcon"
                  mode="aspectFit"
                />
              </view>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="sortOptions"
            range-key="label"
            :value="selectedSortIndex"
            @tap="openPicker('sort')"
            @cancel="closePicker"
            @change="handleSortChange"
          >
            <view class="filter-control">
              <text class="picker-caption">排序</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedSortLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'sort' }"
                  :src="filterArrowIcon"
                  mode="aspectFit"
                />
              </view>
            </view>
          </picker>
          <button class="clear-filter-button" @tap="clearFilters">
            <image class="clear-filter-icon" :src="clearFilterIcon" mode="aspectFit" />
            <text>清除筛选</text>
          </button>
        </view>
      </view>

      <scroll-view
        class="cats-scroll"
        scroll-y
        refresher-enabled
        :refresher-triggered="isRefreshing"
        lower-threshold="180"
        :show-scrollbar="false"
        @refresherrefresh="refreshPage"
        @scrolltolower="loadMoreCats"
      >
        <view class="cats-list-body">
        <view v-if="isLoading && cats.length === 0" class="state-panel">
          <text class="state-title">正在加载猫咪档案...</text>
        </view>
        <view v-else-if="errorMessage && cats.length === 0" class="state-panel is-error" @tap="loadCatsPage">
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
              lazy-load
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

          <view class="list-footer">
            <text v-if="isLoadingMore">正在加载更多猫咪...</text>
            <text v-else-if="!hasMore">已展示全部 {{ totalCats }} 只猫咪</text>
          </view>
        </view>
      </view>
      </scroll-view>
    </view>
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
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import {
  buildCatListQuery,
  buildCatStatsDisplayItems,
  formatCatSeenTime,
  getCatTagTone,
  normalizeCatStats,
} from "./cats-page";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";
import titleMascotIcon from "../../../素材/svg/萌猫/寿司.svg";
import totalStatsIcon from "../../../素材/svg/猫咪库/总计.svg";
import activeStatsIcon from "../../../素材/svg/猫咪库/盾牌.svg";
import waitingAdoptionStatsIcon from "../../../素材/svg/猫咪库/未领养.svg";
import neuteredStatsIcon from "../../../素材/svg/猫咪库/领养.svg";
import graduatedStatsIcon from "../../../素材/svg/猫咪库/星球.svg";
import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import clearFilterIcon from "../../../素材/svg/猫咪库/删除.svg";

type PickerChangeEvent = {
  detail: {
    value: string | number;
  };
};

type PickerKind = "filter_key" | "filter_value" | "sort";

const PAGE_SIZE = 10;
const DEFAULT_SORT_OPTION: CatSortOption = { value: "last_seen_desc", label: "最近出现" };
const statIconMap: Record<string, string> = {
  total: totalStatsIcon,
  active: activeStatsIcon,
  waiting_adoption: waitingAdoptionStatsIcon,
  adopted: neuteredStatsIcon,
  graduated: graduatedStatsIcon,
};

const userStore = useUserStore();
const stats = ref<CatStatsResponse | null>(null);
const filterOptions = ref<CatFilterOption[]>([]);
const sortOptions = ref<CatSortOption[]>([DEFAULT_SORT_OPTION]);
const cats = ref<CatListItemDto[]>([]);
const keyword = ref("");
const selectedFilterKey = ref("");
const selectedFilterValue = ref("");
const selectedSort = ref(DEFAULT_SORT_OPTION.value);
const currentPage = ref(1);
const totalCats = ref(0);
const hasMore = ref(false);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const isRefreshing = ref(false);
const errorMessage = ref("");
const imageFailedIds = ref<string[]>([]);
const activePicker = ref<PickerKind | "">("");

const resolvedStats = computed(() => normalizeCatStats(stats.value));
const statsItems = computed(() => buildCatStatsDisplayItems(stats.value));

const filterKeyPickerOptions = computed(() => [
  { key: "", label: "全部", values: [] },
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
  () => filterKeyPickerOptions.value[selectedFilterKeyIndex.value]?.label ?? "全部",
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

async function loadCatsList(accessToken?: string, options: { reset?: boolean } = { reset: true }) {
  const reset = options.reset ?? true;
  if (!reset && (isLoading.value || isLoadingMore.value || !hasMore.value)) {
    return;
  }

  const token = accessToken ?? await resolveAccessToken();
  if (!token) {
    return;
  }

  const nextPage = reset ? 1 : currentPage.value + 1;
  if (!reset) {
    isLoadingMore.value = true;
  }

  try {
    const response = await getCats(
      token,
      buildCatListQuery({
        keyword: keyword.value,
        filter_key: selectedFilterKey.value,
        filter_value: selectedFilterValue.value,
        sort: selectedSort.value,
        page: nextPage,
        page_size: PAGE_SIZE,
      }),
    );
    const existingIds = new Set(cats.value.map((cat) => cat.cat_id));
    cats.value = reset
      ? response.items
      : [
          ...cats.value,
          ...response.items.filter((cat) => !existingIds.has(cat.cat_id)),
        ];
    currentPage.value = response.page;
    totalCats.value = response.total;
    hasMore.value = response.has_more;
    if (reset) {
      imageFailedIds.value = [];
    }
  } finally {
    isLoadingMore.value = false;
  }
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
    currentPage.value = listResponse.page;
    totalCats.value = listResponse.total;
    hasMore.value = listResponse.has_more;
    imageFailedIds.value = [];
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
    await loadCatsList(undefined, { reset: true });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "猫咪列表刷新失败";
  }
}

async function loadMoreCats() {
  if (isLoading.value || isLoadingMore.value || !hasMore.value) {
    return;
  }

  try {
    await loadCatsList(undefined, { reset: false });
  } catch (error) {
    const message = error instanceof Error ? error.message : "加载更多失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

function openPicker(kind: PickerKind) {
  activePicker.value = kind;
}

function closePicker() {
  activePicker.value = "";
}

function pickerIndex(event: PickerChangeEvent) {
  return Number(event.detail.value) || 0;
}

function handleFilterKeyChange(event: PickerChangeEvent) {
  const selected = filterKeyPickerOptions.value[pickerIndex(event)];
  selectedFilterKey.value = selected?.key ?? "";
  selectedFilterValue.value = "";
  closePicker();
  void handleSearchConfirm();
}

function handleFilterValueChange(event: PickerChangeEvent) {
  const selected = filterValuePickerOptions.value[pickerIndex(event)];
  selectedFilterValue.value = selected?.value ?? "";
  closePicker();
  void handleSearchConfirm();
}

function handleSortChange(event: PickerChangeEvent) {
  const selected = sortOptions.value[pickerIndex(event)];
  selectedSort.value = selected?.value ?? DEFAULT_SORT_OPTION.value;
  closePicker();
  void handleSearchConfirm();
}

function clearFilters() {
  keyword.value = "";
  selectedFilterKey.value = "";
  selectedFilterValue.value = "";
  selectedSort.value = DEFAULT_SORT_OPTION.value;
  closePicker();
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

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  void loadCatsPage();
});
</script>

<style scoped>
.cats-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background: #f7fbef;
  color: #151a20;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.cats-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 24rpx;
}

.cats-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx) calc(env(safe-area-inset-bottom) + 44rpx);
  display: flex;
  flex-direction: column;
}

.cats-fixed {
  flex: 0 0 auto;
}

.cats-list-body {
  padding-bottom: 24rpx;
}

.page-title {
  margin-bottom: 28rpx;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--catmap-page-title-gap, 14rpx);
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

.button-hover {
  transform: translateY(2rpx);
  opacity: 0.9;
}

.title-copy {
  min-width: 0;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.page-title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.page-title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
  transform: scale(1.55);
  transform-origin: center;
}

.page-title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.stats-card,
.search-box,
.filter-card,
.cat-card,
.state-panel {
  box-sizing: border-box;
  border: 2rpx solid rgba(197, 230, 193, 0.78);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
}

.stats-card {
  position: relative;
  min-height: 246rpx;
  overflow: hidden;
  border-radius: 28rpx;
  padding: 30rpx 34rpx 24rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 42rpx rgba(34, 83, 40, 0.12);
}

.stats-card::before {
  position: absolute;
  inset: 0;
  content: "";
  background:
    radial-gradient(circle at 95% 100%, rgba(141, 219, 111, 0.5) 0, rgba(141, 219, 111, 0.32) 92rpx, rgba(141, 219, 111, 0) 190rpx),
    radial-gradient(circle at 88% 0, rgba(207, 239, 192, 0.45) 0, rgba(207, 239, 192, 0) 120rpx),
    linear-gradient(140deg, rgba(248, 255, 246, 0.95) 0%, rgba(255, 255, 255, 0.88) 58%, rgba(232, 248, 221, 0.82) 100%);
  pointer-events: none;
}

.stats-card::after {
  position: absolute;
  right: -54rpx;
  bottom: -84rpx;
  width: 286rpx;
  height: 170rpx;
  border-radius: 60% 40% 0 0;
  background: linear-gradient(135deg, rgba(144, 212, 113, 0.15), rgba(104, 192, 88, 0.52));
  content: "";
  transform: rotate(-8deg);
}

.stats-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  align-items: start;
  gap: 0;
}

.stat-item {
  position: relative;
  min-width: 0;
  text-align: center;
}

.stat-item + .stat-item::before {
  position: absolute;
  top: 8rpx;
  bottom: 0;
  left: 0;
  width: 2rpx;
  background: rgba(170, 198, 164, 0.32);
  content: "";
}

.stat-icon,
.stat-icon-placeholder {
  width: 42rpx;
  height: 42rpx;
}

.stat-icon-green {
  filter: brightness(0) saturate(100%) invert(46%) sepia(89%) saturate(466%) hue-rotate(83deg) brightness(90%) contrast(91%);
}

.stat-icon-orange {
  filter: brightness(0) saturate(100%) invert(59%) sepia(89%) saturate(1228%) hue-rotate(347deg) brightness(98%) contrast(95%);
}

.stat-icon-blue {
  filter: brightness(0) saturate(100%) invert(52%) sepia(90%) saturate(1755%) hue-rotate(189deg) brightness(96%) contrast(91%);
}

.stat-icon-purple {
  filter: brightness(0) saturate(100%) invert(53%) sepia(67%) saturate(2018%) hue-rotate(222deg) brightness(99%) contrast(93%);
}

.stat-value,
.stat-label {
  display: block;
}

.stat-label {
  margin-top: 14rpx;
  color: #1f2933;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.12;
}

.stat-value {
  margin-top: 10rpx;
  font-size: 42rpx;
  font-weight: 900;
  line-height: 1;
}

.stat-value-green {
  color: #14952f;
}

.stat-value-orange {
  color: #f47b1c;
}

.stat-value-blue {
  color: #2f8be6;
}

.stat-value-purple {
  color: #7656ed;
}

.neuter-rate-row {
  position: relative;
  z-index: 2;
  margin-top: 28rpx;
  border-top: 2rpx dashed rgba(180, 204, 174, 0.45);
  padding-top: 16rpx;
  color: #111827;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8rpx;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1;
  text-align: center;
}

.neuter-count {
  color: #129735;
  font-size: 42rpx;
  font-weight: 900;
}

.search-box,
.filter-card,
.cat-card,
.state-panel {
  background: rgba(255, 255, 255, 0.93);
}

.search-box {
  min-height: 72rpx;
  margin-top: 28rpx;
  border: 0;
  border-radius: 24rpx;
  padding: 0 14rpx 0 24rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.search-icon {
  color: #323946;
  font-size: 36rpx;
  line-height: 1;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 72rpx;
  color: #222831;
  font-size: 25rpx;
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
  margin-top: 28rpx;
  border-radius: 26rpx;
  padding: 20rpx 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 82rpx;
  align-items: end;
  gap: 12rpx;
}

.filter-picker {
  min-width: 0;
}

.filter-control {
  min-width: 0;
}

.picker-caption {
  display: block;
  margin: 0 0 10rpx 14rpx;
  color: rgba(82, 90, 102, 0.68);
  font-size: 19rpx;
  font-weight: 800;
  line-height: 1;
}

.picker-shell {
  height: 58rpx;
  box-sizing: border-box;
  border: 2rpx solid #c4dac2;
  border-radius: 19rpx;
  padding: 0 12rpx 0 16rpx;
  background: rgba(255, 255, 255, 0.82);
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.picker-value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #151a20;
  font-size: 21rpx;
  font-weight: 900;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow-icon {
  width: 21rpx;
  height: 21rpx;
  flex: 0 0 auto;
  transform: rotate(180deg);
  transition: transform 0.2s ease;
}

.picker-arrow-icon.is-open {
  transform: rotate(0deg);
}

.clear-filter-button {
  height: 82rpx;
  color: #0d9b2e;
  font-size: 18rpx;
  font-weight: 900;
  line-height: 1.1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 8rpx;
}

.clear-filter-icon {
  width: 32rpx;
  height: 32rpx;
  filter: brightness(0) saturate(100%) invert(37%) sepia(92%) saturate(1118%) hue-rotate(111deg) brightness(93%) contrast(95%);
}

.state-panel {
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

.list-footer {
  min-height: 52rpx;
  color: #6a7480;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 52rpx;
  text-align: center;
}
</style>
