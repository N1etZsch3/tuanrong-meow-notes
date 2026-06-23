<template>
  <view
    class="map-page"
    :class="{
      'drawer-collapsed': drawerState === 'collapsed',
      'is-searching': isSearchMode,
    }"
  >
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />

    <view class="map-title">
      <view class="title-row">
        <text class="title-text">猫协地图</text>
        <image class="title-paw" :src="pawIcon" mode="aspectFit" />
      </view>
      <text class="title-subtitle">探索校园 · 守护猫咪</text>
    </view>

    <view class="map-viewport">
      <view v-if="supportsAmapWeb" id="campus-amap" class="amap-host" />
      <map
        v-else
        class="native-map"
        :longitude="HBNU_CAMPUS.center.lng"
        :latitude="HBNU_CAMPUS.center.lat"
        :scale="17"
        :show-location="false"
        :enable-zoom="true"
        :enable-scroll="true"
      />

      <view v-if="mapLoadState !== 'ready'" class="map-placeholder">
        <text class="placeholder-title">
          {{ mapLoadState === "error" ? "高德地图暂未加载" : "正在加载高德地图" }}
        </text>
        <text class="placeholder-desc">
          {{ mapLoadState === "error" ? "请检查网络或高德前端 Key 配置" : "地图会默认定位到湖北师范大学" }}
        </text>
      </view>

      <view class="filter-wrap">
        <button
          class="filter-chip"
          hover-class="filter-chip-hover"
          @tap="toggleFilterMenu"
        >
          <text class="filter-placeholder-icon">筛</text>
          <text class="filter-label">{{ activeFilterLabel }}</text>
          <text class="filter-chevron" :class="{ 'is-open': filterMenuOpen }">⌄</text>
        </button>
        <view v-if="filterMenuOpen" class="filter-menu">
          <button
            v-for="option in MAP_FILTER_OPTIONS"
            :key="option.key"
            class="filter-option"
            :class="{ 'is-active': option.key === activeFilter }"
            @tap="selectFilter(option.key)"
          >
            <text class="filter-option-title">{{ option.label }}</text>
            <text class="filter-option-desc">{{ option.description }}</text>
          </button>
        </view>
      </view>

      <button class="my-location-btn" hover-class="map-button-hover" @tap="locateMe">
        <image class="my-location-icon" :src="locationIcon" mode="aspectFit" />
        <text>我的位置</text>
      </button>
    </view>

    <view class="content-drawer">
      <view
        class="drawer-grip-area"
        @tap="toggleDrawer"
        @touchstart="handleGripTouchStart"
        @touchend="handleGripTouchEnd"
      >
        <view class="drawer-grip" />
      </view>

      <view class="search-box" :class="{ 'is-focused': isSearchMode }" @tap="focusSearch">
        <text class="search-icon">⌕</text>
        <input
          v-model="searchKeyword"
          class="search-input"
          confirm-type="search"
          placeholder="搜索点位、地标、地址"
          placeholder-class="search-placeholder"
          @focus="focusSearch"
          @confirm="selectFirstSearchResult"
        />
        <button
          v-if="searchKeyword"
          class="clear-search"
          hover-class="clear-search-hover"
          @tap.stop="clearSearch"
        >
          ×
        </button>
      </view>

      <view class="drawer-body">
        <view v-if="isSearchMode" class="section-head">
          <text class="section-title">搜索结果</text>
          <text class="section-action">{{ visibleItems.length }} 个结果</text>
        </view>
        <view v-else class="section-head">
          <text class="section-title">最新任务</text>
          <text class="section-action">后端接入后查看全部</text>
        </view>

        <view v-if="visibleItems.length" class="content-list">
          <button
            v-for="item in visibleItems"
            :key="item.id"
            class="content-row"
            hover-class="content-row-hover"
            @tap="selectShellItem(item)"
          >
            <view class="item-icon" :class="`item-icon-${item.type}`">
              <text>{{ getItemSymbol(item.type) }}</text>
            </view>
            <view class="item-main">
              <text class="item-title">{{ item.title }}</text>
              <view class="item-meta">
                <text class="item-tag" :class="`tag-${item.type}`">
                  {{ item.tag_label || getItemTypeLabel(item.type) }}
                </text>
                <text>· 距离 {{ formatDistance(item.distance_meters) }}</text>
              </view>
            </view>
            <text class="item-status" :class="`status-${item.type}`">
              {{ item.status_label || "查看" }}
            </text>
          </button>
        </view>

        <view v-else class="empty-search">
          <text class="empty-title">没有找到相关点位</text>
          <text class="empty-desc">可以换个关键词，例如“北门”“小橘”“猫粮”。</text>
        </view>
      </view>
    </view>

    <AppTabBar active-key="map" />
  </view>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import AppTabBar from "@/components/AppTabBar.vue";
import { appEnv } from "@/config/app-env";

import locationIcon from "../../../素材/svg/菜单/定位.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/加载页背景.png";
import {
  ALL_MAP_FILTER_KEY,
  HBNU_CAMPUS,
  MAP_FILTER_OPTIONS,
  MAP_SHELL_ITEMS,
  formatDistance,
  getMapDrawerStateAfterDrag,
  getMapFilterLabel,
  searchMapShellItems,
  type MapDrawerState,
  type MapFilterKey,
  type MapShellItem,
  type MapShellItemType,
} from "./map-page";

type MapLoadState = "idle" | "loading" | "ready" | "error";

const drawerState = ref<MapDrawerState>("expanded");
const filterMenuOpen = ref(false);
const activeFilter = ref<MapFilterKey>(ALL_MAP_FILTER_KEY);
const searchKeyword = ref("");
const dragStartY = ref<number | null>(null);
const mapLoadState = ref<MapLoadState>("idle");
const supportsAmapWeb = typeof window !== "undefined" && typeof document !== "undefined";

let amapInstance: any = null;
let amapScriptElement: HTMLScriptElement | null = null;

const isSearchMode = computed(() => searchKeyword.value.trim().length > 0);
const activeFilterLabel = computed(() => getMapFilterLabel(activeFilter.value));
const visibleItems = computed(() => {
  const items = searchMapShellItems(
    MAP_SHELL_ITEMS,
    searchKeyword.value,
    activeFilter.value,
  );

  return isSearchMode.value ? items : items.filter((item) => item.type.includes("task"));
});

function toggleFilterMenu() {
  filterMenuOpen.value = !filterMenuOpen.value;
}

function selectFilter(filterKey: MapFilterKey) {
  activeFilter.value = filterKey;
  filterMenuOpen.value = false;
}

function toggleDrawer() {
  drawerState.value = drawerState.value === "collapsed" ? "expanded" : "collapsed";
}

function handleGripTouchStart(event: Event) {
  const touch = (event as TouchEvent).touches?.[0];
  dragStartY.value = touch?.clientY ?? null;
}

function handleGripTouchEnd(event: Event) {
  const startY = dragStartY.value;
  const touch = (event as TouchEvent).changedTouches?.[0];
  dragStartY.value = null;

  if (startY === null || !touch) {
    return;
  }

  drawerState.value = getMapDrawerStateAfterDrag(
    drawerState.value,
    touch.clientY - startY,
  );
}

function focusSearch() {
  drawerState.value = "expanded";
}

function clearSearch() {
  searchKeyword.value = "";
}

function selectFirstSearchResult() {
  const firstItem = visibleItems.value[0];
  if (firstItem) {
    selectShellItem(firstItem);
  }
}

function selectShellItem(item: MapShellItem) {
  uni.showToast({
    title: `${item.title} 后续接入详情`,
    icon: "none",
  });
}

function getItemTypeLabel(type: MapShellItemType): string {
  return getMapFilterLabel(type);
}

function getItemSymbol(type: MapShellItemType): string {
  const symbols: Record<MapShellItemType, string> = {
    cat: "猫",
    supply: "物",
    daily_task: "任",
    emergency_task: "!",
    landmark: "地",
  };

  return symbols[type];
}

function centerMapToCampus() {
  if (!amapInstance || !window.AMap) {
    return;
  }

  amapInstance.setZoomAndCenter(HBNU_CAMPUS.default_zoom, [
    HBNU_CAMPUS.center.lng,
    HBNU_CAMPUS.center.lat,
  ]);
}

function initializeAmap() {
  if (!supportsAmapWeb || !appEnv.amapWebKey) {
    mapLoadState.value = "error";
    return;
  }

  if (window.AMap) {
    mountAmap();
    return;
  }

  mapLoadState.value = "loading";
  window._AMapSecurityConfig = appEnv.amapSecurityJsCode
    ? { securityJsCode: appEnv.amapSecurityJsCode }
    : undefined;
  window.__initCampusCatMap = mountAmap;

  amapScriptElement = document.createElement("script");
  amapScriptElement.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(
    appEnv.amapWebKey,
  )}&plugin=AMap.Geolocation&callback=__initCampusCatMap`;
  amapScriptElement.onerror = () => {
    mapLoadState.value = "error";
  };
  document.head.appendChild(amapScriptElement);
}

function mountAmap() {
  if (!window.AMap) {
    mapLoadState.value = "error";
    return;
  }

  amapInstance = new window.AMap.Map("campus-amap", {
    center: [HBNU_CAMPUS.center.lng, HBNU_CAMPUS.center.lat],
    zoom: HBNU_CAMPUS.default_zoom,
    zooms: [HBNU_CAMPUS.min_zoom, HBNU_CAMPUS.max_zoom],
    viewMode: "2D",
    resizeEnable: true,
    dragEnable: true,
    zoomEnable: true,
    doubleClickZoom: true,
    keyboardEnable: false,
    showLabel: true,
    mapStyle: "amap://styles/fresh",
  });

  const limitBounds = new window.AMap.Bounds(
    [
      HBNU_CAMPUS.limit_bounds.south_west.lng,
      HBNU_CAMPUS.limit_bounds.south_west.lat,
    ],
    [
      HBNU_CAMPUS.limit_bounds.north_east.lng,
      HBNU_CAMPUS.limit_bounds.north_east.lat,
    ],
  );
  amapInstance.setLimitBounds(limitBounds);
  mapLoadState.value = "ready";
}

function locateMe() {
  if (!supportsAmapWeb) {
    uni.getLocation({
      type: "gcj02",
      success: (location) => {
        uni.showToast({
          title: `已获取位置 ${location.latitude.toFixed(4)}`,
          icon: "none",
        });
      },
      fail: () => {
        uni.showToast({ title: "无法获取当前位置", icon: "none" });
      },
    });
    return;
  }

  if (!window.AMap || !amapInstance) {
    centerMapToCampus();
    uni.showToast({ title: "地图加载后可定位", icon: "none" });
    return;
  }

  window.AMap.plugin("AMap.Geolocation", () => {
    const geolocation = new window.AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 10000,
      zoomToAccuracy: true,
      showMarker: false,
      showCircle: false,
    });
    geolocation.getCurrentPosition((status: string, result: any) => {
      if (status === "complete" && result?.position) {
        amapInstance.setZoomAndCenter(HBNU_CAMPUS.default_zoom, result.position);
        uni.showToast({ title: "已定位到当前位置", icon: "none" });
        return;
      }

      centerMapToCampus();
      uni.showToast({ title: "定位失败，已回到校园中心", icon: "none" });
    });
  });
}

onMounted(() => {
  if (supportsAmapWeb) {
    initializeAmap();
  } else {
    mapLoadState.value = "ready";
  }
});

onBeforeUnmount(() => {
  if (amapInstance?.destroy) {
    amapInstance.destroy();
  }

  if (window.__initCampusCatMap === mountAmap) {
    window.__initCampusCatMap = undefined;
  }

  if (amapScriptElement?.parentNode) {
    amapScriptElement.parentNode.removeChild(amapScriptElement);
  }
});
</script>

<style scoped>
.map-page {
  position: relative;
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  background: #f7fbef;
  color: #111827;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.map-title {
  position: absolute;
  z-index: 3;
  top: 46rpx;
  left: 42rpx;
  right: 42rpx;
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.drawer-collapsed .map-title {
  opacity: 0;
  transform: translateY(-28rpx);
  pointer-events: none;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.title-text {
  color: #111827;
  font-size: 58rpx;
  font-weight: 900;
  letter-spacing: 1rpx;
  line-height: 1;
}

.title-paw {
  width: 54rpx;
  height: 54rpx;
}

.title-subtitle {
  display: block;
  margin-top: 22rpx;
  color: #6b7280;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.2;
}

.map-viewport {
  position: absolute;
  z-index: 1;
  left: 24rpx;
  right: 24rpx;
  top: 194rpx;
  bottom: 646rpx;
  overflow: hidden;
  border-radius: 28rpx;
  background: rgba(228, 244, 218, 0.9);
  box-shadow: 0 14rpx 40rpx rgba(36, 75, 35, 0.12);
  transition: top 0.26s ease, bottom 0.26s ease, border-radius 0.26s ease;
}

.drawer-collapsed .map-viewport {
  left: 0;
  right: 0;
  top: 0;
  bottom: 288rpx;
  border-radius: 0 0 28rpx 28rpx;
}

.amap-host,
.native-map {
  width: 100%;
  height: 100%;
}

.map-placeholder {
  position: absolute;
  inset: 0;
  z-index: 2;
  box-sizing: border-box;
  padding: 44rpx;
  background: linear-gradient(145deg, rgba(236, 249, 228, 0.88), rgba(255, 255, 255, 0.68));
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14rpx;
}

.placeholder-title {
  color: #267b2f;
  font-size: 32rpx;
  font-weight: 900;
}

.placeholder-desc {
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.5;
}

.filter-wrap {
  position: absolute;
  z-index: 5;
  left: 28rpx;
  top: 34rpx;
}

.filter-chip {
  height: 78rpx;
  min-width: 208rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 30rpx rgba(20, 28, 40, 0.12);
  color: #161c28;
  display: flex;
  align-items: center;
  gap: 14rpx;
  line-height: 1;
}

.filter-chip::after,
.filter-option::after,
.content-row::after,
.my-location-btn::after,
.clear-search::after {
  border: 0;
}

.filter-chip-hover,
.map-button-hover,
.content-row-hover {
  opacity: 0.88;
  transform: translateY(2rpx);
}

.filter-placeholder-icon {
  width: 34rpx;
  height: 34rpx;
  border-radius: 10rpx;
  border: 3rpx solid #2b3340;
  color: #2b3340;
  font-size: 18rpx;
  font-weight: 900;
  line-height: 34rpx;
}

.filter-label {
  font-size: 27rpx;
  font-weight: 900;
}

.filter-chevron {
  color: #111827;
  font-size: 28rpx;
  transition: transform 0.18s ease;
}

.filter-chevron.is-open {
  transform: rotate(180deg);
}

.filter-menu {
  width: 316rpx;
  margin-top: 14rpx;
  padding: 12rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 38rpx rgba(20, 28, 40, 0.13);
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.filter-option {
  margin: 0;
  padding: 14rpx 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #2a313d;
  line-height: 1.2;
  text-align: left;
}

.filter-option.is-active {
  background: #edf8e8;
  color: #267b2f;
}

.filter-option-title {
  display: block;
  font-size: 25rpx;
  font-weight: 900;
}

.filter-option-desc {
  display: block;
  margin-top: 6rpx;
  color: #7a818c;
  font-size: 20rpx;
  font-weight: 700;
}

.my-location-btn {
  position: absolute;
  z-index: 5;
  right: 26rpx;
  bottom: 34rpx;
  width: 112rpx;
  height: 112rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 14rpx 34rpx rgba(20, 28, 40, 0.12);
  color: #267b2f;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.my-location-icon {
  width: 42rpx;
  height: 42rpx;
}

.content-drawer {
  position: absolute;
  z-index: 8;
  left: 24rpx;
  right: 24rpx;
  bottom: 150rpx;
  height: 500rpx;
  box-sizing: border-box;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 -8rpx 36rpx rgba(26, 52, 30, 0.12);
  padding: 0 24rpx 24rpx;
  overflow: hidden;
  transition: height 0.26s ease, border-radius 0.26s ease;
}

.drawer-collapsed .content-drawer {
  height: 132rpx;
}

.drawer-grip-area {
  height: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drawer-grip {
  width: 74rpx;
  height: 9rpx;
  border-radius: 999rpx;
  background: #d1d5db;
}

.search-box {
  height: 78rpx;
  box-sizing: border-box;
  border: 2rpx solid rgba(17, 24, 39, 0.08);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.95);
  display: grid;
  grid-template-columns: 38rpx minmax(0, 1fr) 38rpx;
  align-items: center;
  gap: 16rpx;
  padding: 0 22rpx;
}

.search-box.is-focused {
  border-color: rgba(63, 153, 66, 0.36);
  box-shadow: 0 10rpx 24rpx rgba(42, 120, 48, 0.08);
}

.search-icon {
  color: #6b7280;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1;
}

.search-input {
  min-width: 0;
  height: 74rpx;
  color: #111827;
  font-size: 27rpx;
  font-weight: 800;
}

.search-placeholder {
  color: #8b919b;
  font-weight: 700;
}

.clear-search {
  width: 38rpx;
  height: 38rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(17, 24, 39, 0.1);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 38rpx;
}

.drawer-body {
  padding-top: 26rpx;
}

.drawer-collapsed .drawer-body {
  display: none;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.section-action {
  color: #7e8591;
  font-size: 23rpx;
  font-weight: 800;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.content-row {
  height: 104rpx;
  box-sizing: border-box;
  margin: 0;
  padding: 14rpx 20rpx;
  border: 2rpx solid rgba(17, 24, 39, 0.06);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  display: grid;
  grid-template-columns: 64rpx minmax(0, 1fr) auto;
  align-items: center;
  gap: 18rpx;
  line-height: 1;
}

.item-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 60rpx;
  text-align: center;
  box-shadow: 0 9rpx 18rpx rgba(17, 24, 39, 0.12);
}

.item-icon-emergency_task {
  background: #ef3038;
}

.item-icon-daily_task {
  background: #2276ff;
}

.item-icon-cat {
  background: #8754e8;
}

.item-icon-supply {
  background: #ff8b22;
}

.item-icon-landmark {
  background: #51ae57;
}

.item-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.item-title {
  color: #111827;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  color: #8b919b;
  font-size: 22rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.item-tag {
  padding: 3rpx 7rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
}

.tag-emergency_task {
  color: #ef3038;
  background: #ffe6e7;
}

.tag-daily_task {
  color: #2276ff;
  background: #e9f2ff;
}

.tag-cat {
  color: #8754e8;
  background: #efe7ff;
}

.tag-supply {
  color: #ff8b22;
  background: #fff0dc;
}

.tag-landmark {
  color: #267b2f;
  background: #e9f8ea;
}

.item-status {
  font-size: 24rpx;
  font-weight: 900;
}

.status-emergency_task {
  color: #ef3038;
}

.status-daily_task {
  color: #2276ff;
}

.status-cat,
.status-supply,
.status-landmark {
  color: #267b2f;
}

.empty-search {
  padding: 42rpx 0 18rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.empty-title {
  color: #111827;
  font-size: 28rpx;
  font-weight: 900;
}

.empty-desc {
  color: #8b919b;
  font-size: 24rpx;
  font-weight: 700;
}
</style>
