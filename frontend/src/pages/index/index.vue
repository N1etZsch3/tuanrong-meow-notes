<template>
  <view
    class="map-page"
    :class="{
      'is-searching': isSearchMode,
    }"
    :drawerConfig="drawerConfig"
    :change:drawerConfig="drawer.init"
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
        :longitude="mapCenter.lng"
        :latitude="mapCenter.lat"
        :scale="Math.round(campusMapConfig.default_zoom)"
        :markers="nativeMapMarkers"
        :show-location="false"
        :enable-zoom="true"
        :enable-scroll="true"
        @markertap="handleNativeMarkerTap"
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
        @tap="drawer.tap"
        @touchstart="drawer.touchstart"
        @touchmove="drawer.touchmove"
        @touchend="drawer.touchend"
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

      <scroll-view class="drawer-body" scroll-y :show-scrollbar="false">
        <view class="section-head">
          <text class="section-title">{{ contentSectionTitle }}</text>
          <text class="section-action">{{ contentSectionAction }}</text>
        </view>

        <view v-if="selectedSummary" class="summary-card">
          <view class="summary-card-head">
            <view class="summary-icon" :class="`item-icon-${summaryType}`">
              <text>{{ getItemSymbol(summaryType) }}</text>
            </view>
            <view class="summary-main">
              <text class="summary-title">{{ selectedSummary.title }}</text>
              <text class="summary-subtitle">{{ selectedSummary.subtitle || selectedSummary.location_name || "校园点位" }}</text>
            </view>
          </view>
          <view v-if="selectedSummary.tags.length" class="summary-tags">
            <text
              v-for="tag in selectedSummary.tags"
              :key="tag"
              class="summary-tag"
            >
              {{ tag }}
            </text>
          </view>
          <text v-if="selectedSummary.description" class="summary-desc">
            {{ selectedSummary.description }}
          </text>
          <view class="summary-location">
            <text>{{ selectedSummary.location_name || "点位位置" }}</text>
            <text v-if="selectedSummary.distance_meters !== null">
              · 距离 {{ formatDistance(selectedSummary.distance_meters) }}
            </text>
          </view>
          <text v-if="selectedSummary.route_instruction" class="summary-route">
            {{ selectedSummary.route_instruction }}
          </text>
          <view class="summary-actions">
            <button
              v-for="action in selectedSummary.actions"
              :key="action.key"
              class="summary-action"
              :class="{ 'is-disabled': !action.enabled }"
              :disabled="!action.enabled"
              hover-class="summary-action-hover"
              @tap="handleSummaryAction(action)"
            >
              {{ action.label }}
            </button>
          </view>
        </view>

        <view v-else-if="contentLoadState === 'loading'" class="content-loading">
          <text class="loading-title">正在加载地图内容...</text>
          <text class="loading-desc">猫猫正在把最新点位叼过来</text>
        </view>

        <view v-else-if="visibleItems.length" class="content-list">
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
          <text class="empty-title">{{ emptyTitle }}</text>
          <text class="empty-desc">{{ emptyDescription }}</text>
        </view>
      </scroll-view>
    </view>

    <AppTabBar active-key="map" />
  </view>
</template>

<script module="drawer" lang="wxs" src="./drawer.wxs"></script>

<script setup lang="ts">
import { onHide, onShow } from "@dcloudio/uni-app";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import {
  getMapBottomContent,
  getMapInit,
  getMapPointNavigation,
  getMapPointSummary,
  getMapPoints,
  searchMap,
  type CardActionDto,
  type MapInitResponse,
  type MapPointMarkerDto,
  type MapPointSummaryResponse,
} from "@/api/map";
import AppTabBar from "@/components/AppTabBar.vue";
import { appEnv } from "@/config/app-env";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";

import catMarkerIcon from "../../../素材/svg/默认/暂时不用/cat-marker.svg";
import emergencyMarkerIcon from "../../../素材/svg/默认/暂时不用/emergency-marker.svg";
import locationIcon from "../../../素材/svg/菜单/定位.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import supplyMarkerIcon from "../../../素材/svg/默认/暂时不用/supply-marker.svg";
import taskMarkerIcon from "../../../素材/svg/默认/暂时不用/task_marker.svg";
import loadingBackground from "../../../素材/加载页素材/加载页背景.png";
import {
  ALL_MAP_FILTER_KEY,
  HBNU_CAMPUS,
  HBNU_CAMPUS_CORE_BOUNDS,
  MAP_FILTER_OPTIONS,
  expandLngLatBounds,
  formatDistance,
  getMapFilterLabel,
  getMapPointQueryByFilter,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  resolveMapShellItemType,
  type MapFilterKey,
  type CampusMapConfig,
  type LngLat,
  type MapShellItem,
  type MapShellItemType,
} from "./map-page";

type MapLoadState = "idle" | "loading" | "ready" | "error";
type ContentLoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const sysInfo = uni.getSystemInfoSync();
const drawerConfig = ref({
  rpxRatio: sysInfo.windowWidth / 750,
  windowHeight: sysInfo.windowHeight,
});
const filterMenuOpen = ref(false);
const activeFilter = ref<MapFilterKey>(ALL_MAP_FILTER_KEY);
const searchKeyword = ref("");
const mapLoadState = ref<MapLoadState>("idle");
const currentDrawerProgress = ref(1);

function onDrawerProgressChange(progress: number) {
  currentDrawerProgress.value = progress;
  // If progress is 0, we could unfocus search if needed, etc.
}
const contentLoadState = ref<ContentLoadState>("idle");
const contentErrorMessage = ref("");
const campusMapConfig = ref<CampusMapConfig>(HBNU_CAMPUS);
const mapCenter = ref<LngLat>({ ...HBNU_CAMPUS.center });
const mapPointMarkers = ref<MapPointMarkerDto[]>([]);
const bottomContentItems = ref<MapShellItem[]>([]);
const searchResultItems = ref<MapShellItem[]>([]);
const selectedSummary = ref<MapPointSummaryResponse | null>(null);
const amapRuntimeConfig = ref({
  web_key: appEnv.amapWebKey,
  security_js_code: appEnv.amapSecurityJsCode,
  map_style: "amap://styles/fresh",
});
const supportsAmapWeb = typeof window !== "undefined" && typeof document !== "undefined";

let amapInstance: any = null;
let amapScriptElement: HTMLScriptElement | null = null;
let amapMarkers: any[] = [];
let searchTimer: ReturnType<typeof setTimeout> | null = null;
let mapRefreshTimer: ReturnType<typeof setTimeout> | null = null;

const isPageVisible = ref(true);
const isSearchMode = computed(() => searchKeyword.value.trim().length > 0);
const activeFilterLabel = computed(() => getMapFilterLabel(activeFilter.value));
const visibleItems = computed(() => {
  const items = isSearchMode.value
    ? searchResultItems.value
    : bottomContentItems.value;

  return items.filter((item) => {
    return activeFilter.value === ALL_MAP_FILTER_KEY || item.type === activeFilter.value;
  });
});
const summaryType = computed<MapShellItemType>(() => {
  const summary = selectedSummary.value;

  return summary
    ? resolveMapShellItemType(summary.point_type, summary.business_type)
    : "landmark";
});
const contentSectionTitle = computed(() => {
  if (selectedSummary.value) {
    return "点位详情";
  }

  if (isSearchMode.value) {
    return "搜索结果";
  }

  return "最新任务";
});
const contentSectionAction = computed(() => {
  if (selectedSummary.value) {
    return "后端卡片数据";
  }

  if (contentLoadState.value === "loading") {
    return "加载中";
  }

  if (isSearchMode.value) {
    return `${visibleItems.value.length} 个结果`;
  }

  return "后端实时数据";
});
const emptyTitle = computed(() => {
  if (contentLoadState.value === "error") {
    return "地图内容加载失败";
  }

  return isSearchMode.value ? "没有找到相关点位" : "暂无地图动态";
});
const emptyDescription = computed(() => {
  if (contentLoadState.value === "error") {
    return contentErrorMessage.value || "请稍后重试，或检查登录状态。";
  }

  return isSearchMode.value
    ? "可以换个关键词，例如“北门”“小橘”“猫粮”。"
    : "后端暂时没有返回最新任务。";
});
const nativeMapMarkers = computed(() => {
  return mapPointMarkers.value.map((marker, index) => {
    const type = resolveMapShellItemType(marker.point_type, marker.business_type);

    return {
      id: index + 1,
      longitude: marker.lng,
      latitude: marker.lat,
      iconPath: getNativeMarkerIcon(type),
      width: 34,
      height: 34,
      callout: {
        content: marker.name,
        color: "#111827",
        fontSize: 12,
        borderRadius: 8,
        bgColor: "#ffffff",
        padding: 8,
        display: "BYCLICK",
      },
    };
  });
});

function toggleFilterMenu() {
  filterMenuOpen.value = !filterMenuOpen.value;
}

function selectFilter(filterKey: MapFilterKey) {
  activeFilter.value = filterKey;
  filterMenuOpen.value = false;
}



function focusSearch() {
  // WXS handles drawer expansion now, we can leave this empty or
  // trigger WXS if needed in the future.
}

function clearSearch() {
  searchKeyword.value = "";
  selectedSummary.value = null;
}

function selectFirstSearchResult() {
  const firstItem = visibleItems.value[0];
  if (firstItem) {
    selectShellItem(firstItem);
  }
}

function selectShellItem(item: MapShellItem) {
  if (item.lng !== undefined && item.lat !== undefined) {
    centerMapToPoint({ lng: item.lng, lat: item.lat });
  }

  if (item.map_point_id) {
    void loadPointSummary(item.map_point_id);
  }
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

function getNativeMarkerIcon(type: MapShellItemType): string {
  const icons: Record<MapShellItemType, string> = {
    emergency_task: emergencyMarkerIcon,
    daily_task: taskMarkerIcon,
    cat: catMarkerIcon,
    supply: supplyMarkerIcon,
    landmark: locationIcon,
  };

  return icons[type];
}

function getMarkerColor(type: MapShellItemType): string {
  const colors: Record<MapShellItemType, string> = {
    emergency_task: "#ef3038",
    daily_task: "#2f7cf6",
    cat: "#8754e8",
    supply: "#ff8b22",
    landmark: "#28a745",
  };

  return colors[type];
}

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  contentLoadState.value = "error";
  contentErrorMessage.value = "请先登录后查看校园地图。";
  uni.showToast({ title: "请先登录", icon: "none" });
  return null;
}

function handleMapError(error: unknown, fallbackMessage: string) {
  if (error instanceof ApiBusinessError) {
    contentErrorMessage.value = error.message;
    if (error.code === 40101 || error.code === 40102 || error.code === 40301) {
      userStore.clearSession();
    }
    return;
  }

  contentErrorMessage.value = fallbackMessage;
}

function centerMapToPoint(point: LngLat) {
  mapCenter.value = { ...point };

  if (supportsAmapWeb && amapInstance) {
    amapInstance.setZoomAndCenter(campusMapConfig.value.default_zoom, [
      point.lng,
      point.lat,
    ]);
  }
}

function centerMapToCampus() {
  mapCenter.value = { ...campusMapConfig.value.center };

  if (supportsAmapWeb && amapInstance) {
    amapInstance.setZoomAndCenter(campusMapConfig.value.default_zoom, [
      campusMapConfig.value.center.lng,
      campusMapConfig.value.center.lat,
    ]);
  }
}

function applyMapInit(data: MapInitResponse) {
  const coreBounds = HBNU_CAMPUS_CORE_BOUNDS;
  campusMapConfig.value = {
    id: data.campus.campus_id,
    name: data.campus.name,
    center: {
      lng: data.campus.center_lng,
      lat: data.campus.center_lat,
    },
    default_zoom: data.campus.default_zoom || HBNU_CAMPUS.default_zoom,
    min_zoom: data.campus.min_zoom || HBNU_CAMPUS.min_zoom,
    max_zoom: data.campus.max_zoom || HBNU_CAMPUS.max_zoom,
    core_bounds: coreBounds,
    limit_bounds: expandLngLatBounds(coreBounds, 0.35),
  };
  mapCenter.value = { ...campusMapConfig.value.center };
  amapRuntimeConfig.value = {
    web_key: data.amap_config?.web_key || appEnv.amapWebKey,
    security_js_code:
      data.amap_config?.security_js_code || appEnv.amapSecurityJsCode,
    map_style: data.amap_config?.map_style || "amap://styles/fresh",
  };
}

function initializeAmap() {
  const webKey = amapRuntimeConfig.value.web_key;

  if (!supportsAmapWeb || !webKey) {
    mapLoadState.value = "error";
    return;
  }

  if (window.AMap) {
    mountAmap();
    return;
  }

  mapLoadState.value = "loading";
  window._AMapSecurityConfig = amapRuntimeConfig.value.security_js_code
    ? { securityJsCode: amapRuntimeConfig.value.security_js_code }
    : undefined;
  window.__initCampusCatMap = mountAmap;

  amapScriptElement = document.createElement("script");
  amapScriptElement.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(
    webKey,
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
    center: [campusMapConfig.value.center.lng, campusMapConfig.value.center.lat],
    zoom: campusMapConfig.value.default_zoom,
    zooms: [campusMapConfig.value.min_zoom, campusMapConfig.value.max_zoom],
    viewMode: "2D",
    resizeEnable: true,
    dragEnable: true,
    zoomEnable: true,
    doubleClickZoom: true,
    keyboardEnable: false,
    showLabel: true,
    mapStyle: amapRuntimeConfig.value.map_style,
  });

  const limitBounds = new window.AMap.Bounds(
    [
      campusMapConfig.value.limit_bounds.south_west.lng,
      campusMapConfig.value.limit_bounds.south_west.lat,
    ],
    [
      campusMapConfig.value.limit_bounds.north_east.lng,
      campusMapConfig.value.limit_bounds.north_east.lat,
    ],
  );
  amapInstance.setLimitBounds(limitBounds);
  amapInstance.on("moveend", scheduleRefreshMapPoints);
  amapInstance.on("zoomend", scheduleRefreshMapPoints);
  mapLoadState.value = "ready";
  renderAmapMarkers();
}

function getViewportQuery() {
  if (supportsAmapWeb && amapInstance?.getBounds) {
    const bounds = amapInstance.getBounds();
    const southWest = bounds.getSouthWest();
    const northEast = bounds.getNorthEast();

    return {
      min_lng: southWest.lng,
      min_lat: southWest.lat,
      max_lng: northEast.lng,
      max_lat: northEast.lat,
    };
  }

  return {
    min_lng: campusMapConfig.value.limit_bounds.south_west.lng,
    min_lat: campusMapConfig.value.limit_bounds.south_west.lat,
    max_lng: campusMapConfig.value.limit_bounds.north_east.lng,
    max_lat: campusMapConfig.value.limit_bounds.north_east.lat,
  };
}

async function refreshMapPoints() {
  if (!isPageVisible.value) {
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    const data = await getMapPoints(token, {
      campus_id: campusMapConfig.value.id,
      ...getMapPointQueryByFilter(activeFilter.value),
      ...getViewportQuery(),
    });
    mapPointMarkers.value = data.items;
    renderAmapMarkers();
  } catch (error) {
    handleMapError(error, "地图点位加载失败");
  }
}

function scheduleRefreshMapPoints() {
  if (mapRefreshTimer) {
    clearTimeout(mapRefreshTimer);
  }

  mapRefreshTimer = setTimeout(() => {
    void refreshMapPoints();
  }, 300);
}

async function loadBottomContent() {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    const data = await getMapBottomContent(token, { mode: "auto", limit: 10 });
    bottomContentItems.value = data.items.map(mapBottomContentItemToShellItem);
  } catch (error) {
    handleMapError(error, "底部动态内容加载失败");
  }
}

async function runSearch(keyword: string) {
  if (!isPageVisible.value) {
    return;
  }

  const normalizedKeyword = keyword.trim();
  if (!normalizedKeyword) {
    searchResultItems.value = [];
    contentLoadState.value = "ready";
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  contentLoadState.value = "loading";
  selectedSummary.value = null;
  try {
    const filterQuery = getMapPointQueryByFilter(activeFilter.value);
    const data = await searchMap(token, {
      keyword: normalizedKeyword,
      campus_id: campusMapConfig.value.id,
      point_types: filterQuery.point_types,
      page: 1,
      page_size: 20,
    });
    searchResultItems.value = data.items
      .map(mapSearchResultToShellItem)
      .filter((item) => {
        return activeFilter.value === ALL_MAP_FILTER_KEY || item.type === activeFilter.value;
      });
    contentLoadState.value = "ready";
  } catch (error) {
    searchResultItems.value = [];
    contentLoadState.value = "error";
    handleMapError(error, "搜索失败，请稍后重试。");
  }
}

async function loadPointSummary(pointId: string) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  contentLoadState.value = "loading";
  try {
    selectedSummary.value = await getMapPointSummary(token, pointId);
    centerMapToPoint({
      lng: selectedSummary.value.lng,
      lat: selectedSummary.value.lat,
    });
    contentLoadState.value = "ready";
  } catch (error) {
    selectedSummary.value = null;
    contentLoadState.value = "error";
    handleMapError(error, "点位详情加载失败");
  }
}

async function handleSummaryAction(action: CardActionDto) {
  if (!action.enabled || !selectedSummary.value) {
    return;
  }

  if (action.key !== "navigate") {
    uni.showToast({ title: `${action.label}功能后续接入`, icon: "none" });
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    const navigation = await getMapPointNavigation(token, selectedSummary.value.point_id);
    if (supportsAmapWeb && navigation.amap_navigation.web_url) {
      window.open(navigation.amap_navigation.web_url, "_blank");
      return;
    }

    uni.showModal({
      title: navigation.title,
      content:
        navigation.route_instruction ||
        navigation.entrance_hint ||
        "已获取导航目标点，可在地图中查看位置。",
      showCancel: false,
    });
  } catch (error) {
    handleMapError(error, "导航信息加载失败");
    uni.showToast({ title: contentErrorMessage.value, icon: "none" });
  }
}

async function loadInitialMapData() {
  const token = await getAccessToken();
  if (!token) {
    mapLoadState.value = "error";
    return;
  }

  contentLoadState.value = "loading";
  try {
    const initData = await getMapInit(token);
    applyMapInit(initData);
    if (supportsAmapWeb) {
      initializeAmap();
    } else {
      mapLoadState.value = "ready";
    }
    await Promise.all([refreshMapPoints(), loadBottomContent()]);
    contentLoadState.value = "ready";
  } catch (error) {
    mapLoadState.value = "error";
    contentLoadState.value = "error";
    handleMapError(error, "地图初始化失败，请稍后重试。");
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function createAmapMarkerContent(item: MapShellItem): string {
  const color = getMarkerColor(item.type);
  const symbol = escapeHtml(getItemSymbol(item.type));
  const title = escapeHtml(item.title);

  return `
    <div style="position:relative;transform:translate(-50%,-100%);">
      <div style="width:34px;height:34px;border-radius:17px;background:${color};color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:15px;box-shadow:0 8px 18px rgba(17,24,39,.18);border:3px solid #fff;">${symbol}</div>
      <div style="position:absolute;left:50%;top:31px;width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:10px solid ${color};transform:translateX(-50%);"></div>
      <div style="position:absolute;left:50%;top:40px;transform:translateX(-50%);max-width:132px;padding:4px 8px;border-radius:9px;background:rgba(255,255,255,.94);color:#111827;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 6px 14px rgba(17,24,39,.13);">${title}</div>
    </div>
  `;
}

function clearAmapMarkers() {
  if (amapInstance && amapMarkers.length) {
    amapInstance.remove(amapMarkers);
  }

  amapMarkers = [];
}

function renderAmapMarkers() {
  if (!supportsAmapWeb || !window.AMap || !amapInstance) {
    return;
  }

  clearAmapMarkers();
  amapMarkers = mapPointMarkers.value.map((marker) => {
    const item = mapMarkerToShellItem(marker);
    const amapMarker = new window.AMap.Marker({
      position: [marker.lng, marker.lat],
      content: createAmapMarkerContent(item),
      zIndex: marker.display_level,
      offset: new window.AMap.Pixel(0, 0),
    });

    amapMarker.on("click", () => {
      centerMapToPoint({ lng: marker.lng, lat: marker.lat });
      void loadPointSummary(marker.point_id);
    });

    return amapMarker;
  });

  if (amapMarkers.length) {
    amapInstance.add(amapMarkers);
  }
}

function handleNativeMarkerTap(event: Event) {
  const markerId = (event as CustomEvent<{ markerId?: number }>).detail?.markerId;
  if (!markerId) {
    return;
  }

  const marker = mapPointMarkers.value[markerId - 1];
  if (!marker) {
    return;
  }

  centerMapToPoint({ lng: marker.lng, lat: marker.lat });
  void loadPointSummary(marker.point_id);
}

function locateMe() {
  if (!supportsAmapWeb) {
    uni.getLocation({
      type: "gcj02",
      success: (location) => {
        mapCenter.value = {
          lng: location.longitude,
          lat: location.latitude,
        };
        void refreshMapPoints();
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
        amapInstance.setZoomAndCenter(
          campusMapConfig.value.default_zoom,
          result.position,
        );
        mapCenter.value = {
          lng: result.position.lng,
          lat: result.position.lat,
        };
        void refreshMapPoints();
        uni.showToast({ title: "已定位到当前位置", icon: "none" });
        return;
      }

      centerMapToCampus();
      uni.showToast({ title: "定位失败，已回到校园中心", icon: "none" });
    });
  });
}

watch(activeFilter, () => {
  selectedSummary.value = null;
  void refreshMapPoints();
  if (isSearchMode.value) {
    void runSearch(searchKeyword.value);
  }
});

watch(searchKeyword, (keyword) => {
  selectedSummary.value = null;
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  if (!keyword.trim()) {
    searchResultItems.value = [];
    contentLoadState.value = "ready";
    return;
  }

  searchTimer = setTimeout(() => {
    void runSearch(keyword);
  }, 300);
});

onMounted(() => {
  void loadInitialMapData();
});

onShow(() => {
  isPageVisible.value = true;
  if (supportsAmapWeb && amapInstance) {
    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
      void refreshMapPoints();
    }, 150);
  } else if (!supportsAmapWeb) {
    void refreshMapPoints();
  }
});

onHide(() => {
  isPageVisible.value = false;
  if (mapRefreshTimer) {
    clearTimeout(mapRefreshTimer);
  }
});

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  if (mapRefreshTimer) {
    clearTimeout(mapRefreshTimer);
  }

  clearAmapMarkers();

  if (amapInstance?.destroy) {
    amapInstance.destroy();
  }

  if (supportsAmapWeb && window.__initCampusCatMap === mountAmap) {
    window.__initCampusCatMap = undefined;
  }

  if (supportsAmapWeb && amapScriptElement?.parentNode) {
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

}

.amap-host,
.native-map {
  width: 100%;
  height: 100%;
}

:deep(.amap-logo),
:deep(.amap-copyright) {
  display: none !important;
  opacity: 0 !important;
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
  display: flex;
  flex-direction: column;
}

.drawer-grip-area {
  height: 36rpx;
  flex-shrink: 0;
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
  flex-shrink: 0;
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
  flex: 1;
  min-height: 0;
  padding-top: 26rpx;
  box-sizing: border-box;
}

.drawer-body ::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
  color: transparent;
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

.content-loading {
  padding: 58rpx 0 32rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.loading-title {
  color: #267b2f;
  font-size: 28rpx;
  font-weight: 900;
}

.loading-desc {
  color: #8b919b;
  font-size: 23rpx;
  font-weight: 700;
}

.summary-card {
  box-sizing: border-box;
  padding: 22rpx;
  border: 2rpx solid rgba(17, 24, 39, 0.06);
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.94);
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.summary-card-head {
  display: grid;
  grid-template-columns: 68rpx minmax(0, 1fr);
  align-items: center;
  gap: 18rpx;
}

.summary-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 64rpx;
  text-align: center;
  box-shadow: 0 9rpx 18rpx rgba(17, 24, 39, 0.12);
}

.summary-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.summary-title {
  color: #111827;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 1.15;
}

.summary-subtitle,
.summary-location {
  color: #7e8591;
  font-size: 23rpx;
  font-weight: 800;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.summary-tag {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #edf8e8;
  color: #267b2f;
  font-size: 20rpx;
  font-weight: 900;
}

.summary-desc,
.summary-route {
  color: #4b5563;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.55;
}

.summary-route {
  padding: 14rpx 16rpx;
  border-radius: 18rpx;
  background: #f5faef;
}

.summary-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.summary-action {
  height: 66rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  border-radius: 20rpx;
  background: #267b2f;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 66rpx;
}

.summary-action::after {
  border: 0;
}

.summary-action.is-disabled {
  background: #d1d5db;
  color: #ffffff;
}

.summary-action-hover {
  opacity: 0.88;
  transform: translateY(2rpx);
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
