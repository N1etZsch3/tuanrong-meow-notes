<template>
  <view
    class="map-page"
    :class="{
      'is-searching': isSearchMode,
    }"
    :drawerConfig="drawerConfig"
    :change:drawerConfig="drawer.init"
    :filterMenuState="filterMenuState"
    :change:filterMenuState="filterMenu.sync"
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
      <map
        class="native-map"
        :longitude="mapCenter.lng"
        :latitude="mapCenter.lat"
        :scale="Math.round(campusMapConfig.default_zoom)"
        :markers="nativeMapMarkers"
        :polyline="nativeMapPolylines"
        :include-points="nativeMapIncludePoints"
        :show-location="Boolean(userLocation)"
        :enable-zoom="true"
        :enable-scroll="true"
        @markertap="handleNativeMarkerTap"
        @longpress="handleMarkerLongPress"
        @regionchange="handleMapRegionChange"
      />

      <view v-if="mapLoadState !== 'ready'" class="map-placeholder">
        <text class="placeholder-title">
          {{ mapLoadState === "error" ? "校园地图暂未加载" : "正在加载校园地图" }}
        </text>
        <text class="placeholder-desc">
          {{ mapLoadState === "error" ? "请检查网络或登录状态" : "地图会默认定位到湖北师范大学" }}
        </text>
      </view>

      <button class="my-location-btn" hover-class="map-button-hover" @tap="locateMe">
        <image class="my-location-icon" :src="locationIcon" mode="aspectFit" />
        <text>我的位置</text>
      </button>

      <view v-if="navigationRoute" class="navigation-panel">
        <view class="navigation-copy">
          <text class="navigation-title">{{ navigationRoute.title }}</text>
          <text class="navigation-meta">
            {{ navigationRouteDistance }} · {{ navigationRouteDuration }}
          </text>
        </view>
        <button
          v-if="!navigationSimulationRunning"
          class="navigation-control"
          hover-class="summary-action-hover"
          @tap="startSimulatedNavigation"
        >
          模拟导航
        </button>
        <button
          v-else
          class="navigation-control is-secondary"
          hover-class="summary-action-hover"
          @tap="stopSimulatedNavigation"
        >
          停止
        </button>
      </view>

      <view v-if="mapPointEditMode" class="map-edit-panel">
        <text class="map-edit-title">点位编辑模式</text>
        <text class="map-edit-desc">
          移动地图后保存中心点：{{ editedPointLocationText }}
        </text>
        <view class="map-edit-actions">
          <button class="map-edit-button" @tap="saveEditedPointLocation">保存位置</button>
          <button class="map-edit-button is-ghost" @tap="cancelMapPointEditMode">
            取消
          </button>
        </view>
      </view>
    </view>

    <cover-view class="map-filter-layer">
      <cover-view class="filter-panel-hit-layer">
        <cover-view
          class="filter-chip"
          hover-class="filter-chip-hover"
          @tap="toggleFilterMenu"
        >
          <cover-image class="filter-chip-icon" :src="activeFilterIcon" />
          <cover-view class="filter-label">{{ activeFilterLabel }}</cover-view>
          <cover-view class="filter-arrow-slot">
            <cover-image class="filter-arrow-icon" :src="filterArrowIcon" />
          </cover-view>
        </cover-view>
        <cover-view class="filter-menu">
          <cover-view
            v-for="option in filterOptions"
            :key="option.key"
            class="filter-option"
            :class="{ 'is-active': option.key === activeFilter }"
            @tap="selectFilter(option)"
          >
            <cover-image
              class="filter-option-icon"
              :src="getFilterOptionIcon(option)"
            />
            <cover-view class="filter-option-copy">
              <cover-view class="filter-option-title">{{ option.label }}</cover-view>
              <cover-view class="filter-option-desc">{{ option.description }}</cover-view>
            </cover-view>
          </cover-view>
        </cover-view>
      </cover-view>
    </cover-view>

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
              v-for="action in summaryActions"
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
<script module="filterMenu" lang="wxs" src="./filter-menu.wxs"></script>

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
  type MapNavigationResponse,
  type MapPointMarkerDto,
  type MapPointSummaryResponse,
} from "@/api/map";
import { updateAdminMapPointLocation } from "@/api/admin-map";
import AppTabBar from "@/components/AppTabBar.vue";
import { ApiBusinessError, isRequestCanceledError } from "@/services/request";
import { useUserStore } from "@/stores/user";

import allMarkerPointIcon from "../../../素材/svg/地图点/全部.svg";
import catPointMarkerIcon from "../../../素材/svg/地图点/猫咪点.svg";
import completedTaskMarkerIcon from "../../../素材/svg/地图点/完成任务.svg";
import dailyTaskPointIcon from "../../../素材/svg/地图点/日常任务.svg";
import emergencyTaskPointIcon from "../../../素材/svg/地图点/紧急任务.svg";
import failedTaskMarkerIcon from "../../../素材/svg/地图点/失败任务.svg";
import filterArrowIcon from "../../../素材/svg/地图点/箭头.svg";
import filterDefaultIcon from "../../../素材/svg/地图点/筛选.svg";
import landmarkPointIcon from "../../../素材/svg/地图点/地标.svg";
import supplyPointMarkerIcon from "../../../素材/svg/地图点/物资点.svg";
import catMarkerIcon from "../../../素材/svg/默认/暂时不用/cat-marker.svg";
import emergencyMarkerIcon from "../../../素材/svg/默认/暂时不用/emergency-marker.svg";
import locationIcon from "../../../素材/svg/菜单/定位.svg";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import supplyMarkerIcon from "../../../素材/svg/默认/暂时不用/supply-marker.svg";
import taskMarkerIcon from "../../../素材/svg/默认/暂时不用/task_marker.svg";
import loadingBackground from "../../../素材/加载页素材/加载页背景.jpg";
import {
  ALL_MAP_FILTER_KEY,
  HBNU_CAMPUS,
  HBNU_CAMPUS_CORE_BOUNDS,
  NO_MAP_FILTER_KEY,
  NO_MAP_FILTER_LABEL,
  NO_MAP_FILTER_OPTION,
  expandLngLatBounds,
  formatDistance,
  getMapFilterLabel,
  getMapPointQueryByFilter,
  isMapShellItemVisibleByFilter,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  normalizeMapFilterOptions,
  type MapFilterOption,
  resolveMapShellItemType,
  type MapFilterKey,
  type CampusMapConfig,
  type LngLat,
  type MapShellItem,
  type MapShellItemType,
} from "./map-page";

type MapLoadState = "idle" | "loading" | "ready" | "error";
type ContentLoadState = "idle" | "loading" | "ready" | "error";
interface NavigationRouteState {
  title: string;
  distance_meters: number | null;
  duration_seconds: number | null;
  points: LngLat[];
  steps: MapNavigationResponse["route"]["steps"];
}

const userStore = useUserStore();
const sysInfo = uni.getSystemInfoSync();
const drawerConfig = ref({
  rpxRatio: sysInfo.windowWidth / 750,
  windowHeight: sysInfo.windowHeight,
});
const filterMenuOpen = ref(false);
const filterOptions = ref<MapFilterOption[]>([NO_MAP_FILTER_OPTION]);
const activeFilter = ref<MapFilterKey | null>(null);
const searchKeyword = ref("");
const mapLoadState = ref<MapLoadState>("idle");
const contentLoadState = ref<ContentLoadState>("idle");
const contentErrorMessage = ref("");
const campusMapConfig = ref<CampusMapConfig>(HBNU_CAMPUS);
const mapCenter = ref<LngLat>({ ...HBNU_CAMPUS.center });
const userLocation = ref<LngLat | null>(null);
const mapPointMarkers = ref<MapPointMarkerDto[]>([]);
const nativeRoutePoints = ref<Array<{ longitude: number; latitude: number }>>([]);
const navigationRoute = ref<NavigationRouteState | null>(null);
const simulatedNavigationMarker = ref<LngLat | null>(null);
const navigationSimulationRunning = ref(false);
const bottomContentItems = ref<MapShellItem[]>([]);
const searchResultItems = ref<MapShellItem[]>([]);
const selectedSummary = ref<MapPointSummaryResponse | null>(null);
const mapPointEditMode = ref(false);
const editedPointLocation = ref<LngLat | null>(null);
const MAP_FILTER_ICON_SRC: Record<string, string> = {
  none: filterDefaultIcon,
  all: allMarkerPointIcon,
  emergency_task: emergencyTaskPointIcon,
  daily_task: dailyTaskPointIcon,
  cat: catPointMarkerIcon,
  supply: supplyPointMarkerIcon,
  landmark: landmarkPointIcon,
  feeding_pending: failedTaskMarkerIcon,
  feeding_completed: completedTaskMarkerIcon,
  filter_none: filterDefaultIcon,
};

let searchTimer: ReturnType<typeof setTimeout> | null = null;
let mapRefreshTimer: ReturnType<typeof setTimeout> | null = null;
let navigationSimulationTimer: ReturnType<typeof setInterval> | null = null;
let navigationSimulationIndex = 0;

const isPageVisible = ref(true);
const isSearchMode = computed(() => searchKeyword.value.trim().length > 0);
const activeFilterOption = computed(() =>
  activeFilter.value
    ? filterOptions.value.find((option) => option.key === activeFilter.value) || null
    : null,
);
const activeFilterLabel = computed(() =>
  activeFilterOption.value?.label ||
  (activeFilter.value ? getMapFilterLabel(activeFilter.value) : NO_MAP_FILTER_LABEL),
);
const activeFilterIcon = computed(() =>
  activeFilterOption.value
    ? getFilterOptionIcon(activeFilterOption.value)
    : filterDefaultIcon,
);
const filterMenuState = computed(() => ({
  open: filterMenuOpen.value,
  rpxRatio: drawerConfig.value.rpxRatio,
}));
const visibleItems = computed(() => {
  const items = isSearchMode.value
    ? searchResultItems.value
    : bottomContentItems.value;

  return items.filter((item) => {
    return (
      !activeFilter.value ||
      activeFilter.value === ALL_MAP_FILTER_KEY ||
      isMapShellItemVisibleByFilter(item, activeFilter.value)
    );
  });
});
const summaryType = computed<MapShellItemType>(() => {
  const summary = selectedSummary.value;

  return summary
    ? resolveMapShellItemType(summary.point_type, summary.business_type)
    : "landmark";
});
const summaryActions = computed<CardActionDto[]>(() => {
  if (!selectedSummary.value) {
    return [];
  }
  const actions = [...selectedSummary.value.actions];
  if (
    userStore.isAdmin &&
    selectedSummary.value.business_type !== "amap_poi" &&
    !actions.some((action) => action.key === "edit_point")
  ) {
    actions.push({
      key: "edit_point",
      label: "编辑点位",
      enabled: true,
      disabled_reason: null,
      method: null,
      path: `/pages/admin/map-point/edit?point_id=${selectedSummary.value.point_id}`,
      target_type: "page",
    });
  }
  return actions;
});
const navigationRouteDistance = computed(() =>
  navigationRoute.value ? formatDistance(navigationRoute.value.distance_meters) : "未知",
);
const navigationRouteDuration = computed(() => {
  const seconds = navigationRoute.value?.duration_seconds;
  if (!seconds) {
    return "预计时间未知";
  }
  return `约 ${Math.max(1, Math.round(seconds / 60))} 分钟`;
});
const editedPointLocationText = computed(() => {
  const point = editedPointLocation.value || selectedSummary.value;
  if (!point) {
    return "未知坐标";
  }
  return `${point.lng.toFixed(6)}, ${point.lat.toFixed(6)}`;
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
  const markers = mapPointMarkers.value.map((marker, index) => {
    const type = resolveMapShellItemType(marker.point_type, marker.business_type);

    return {
      id: index + 1,
      longitude: marker.lng,
      latitude: marker.lat,
      iconPath: getNativeMarkerIcon(type, marker),
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
  if (simulatedNavigationMarker.value) {
    markers.push({
      id: 900001,
      longitude: simulatedNavigationMarker.value.lng,
      latitude: simulatedNavigationMarker.value.lat,
      iconPath: locationIcon,
      width: 32,
      height: 32,
      callout: {
        content: "当前位置",
        color: "#267b2f",
        fontSize: 12,
        borderRadius: 8,
        bgColor: "#ffffff",
        padding: 8,
        display: "ALWAYS",
      },
    });
  }
  if (mapPointEditMode.value && editedPointLocation.value) {
    markers.push({
      id: 900002,
      longitude: editedPointLocation.value.lng,
      latitude: editedPointLocation.value.lat,
      iconPath: locationIcon,
      width: 38,
      height: 38,
      callout: {
        content: "编辑位置",
        color: "#111827",
        fontSize: 12,
        borderRadius: 8,
        bgColor: "#ffffff",
        padding: 8,
        display: "ALWAYS",
      },
    });
  }
  return markers;
});
const nativeMapPolylines = computed(() => {
  if (nativeRoutePoints.value.length < 2) {
    return [];
  }

  return [
    {
      points: nativeRoutePoints.value,
      color: "#267b2fCC",
      width: 6,
      dottedLine: false,
      arrowLine: true,
      borderColor: "#ffffff",
      borderWidth: 2,
    },
  ];
});
const nativeMapIncludePoints = computed(() => {
  if (nativeRoutePoints.value.length) {
    return nativeRoutePoints.value;
  }

  return mapPointMarkers.value.map((marker) => ({
    longitude: marker.lng,
    latitude: marker.lat,
  }));
});

function selectFilter(option: MapFilterOption) {
  activeFilter.value = option.key === NO_MAP_FILTER_KEY ? null : option.key;
  filterMenuOpen.value = false;
}

function toggleFilterMenu() {
  filterMenuOpen.value = !filterMenuOpen.value;
}

function getFilterOptionIcon(option: MapFilterOption): string {
  return MAP_FILTER_ICON_SRC[option.icon_key || option.key] || filterDefaultIcon;
}



function focusSearch() {
  // WXS handles drawer expansion now, we can leave this empty or
  // trigger WXS if needed in the future.
}

function clearSearch() {
  searchKeyword.value = "";
  searchResultItems.value = [];
  selectedSummary.value = null;
  clearSearchResultMarkers();
}

function clearSearchResultMarkers() {
  if (activeFilter.value) {
    return;
  }

  mapPointMarkers.value = [];
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
    return;
  }

  selectedSummary.value = buildExternalSummaryFromItem(item);
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

function getFeedingMarkerIcon(marker: MapPointMarkerDto): string {
  return marker.extra.feeding_status === "completed"
    ? completedTaskMarkerIcon
    : failedTaskMarkerIcon;
}

function getNativeMarkerIcon(
  type: MapShellItemType,
  marker?: MapPointMarkerDto,
): string {
  if (marker && marker.business_type === "feeding") {
    return getFeedingMarkerIcon(marker);
  }

  const icons: Record<MapShellItemType, string> = {
    emergency_task: emergencyMarkerIcon,
    daily_task: taskMarkerIcon,
    cat: catMarkerIcon,
    supply: supplyMarkerIcon,
    landmark: locationIcon,
  };

  return icons[type];
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
  if (isRequestCanceledError(error)) {
    return;
  }

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
}

function centerMapToCampus() {
  mapCenter.value = { ...campusMapConfig.value.center };
}

function setUserLocation(point: LngLat) {
  userLocation.value = point;
}

function getCurrentLocationForNavigation(): Promise<LngLat | null> {
  if (userLocation.value) {
    return Promise.resolve(userLocation.value);
  }

  return new Promise((resolve) => {
    uni.getLocation({
      type: "gcj02",
      success: (location) => {
        const point = {
          lng: location.longitude,
          lat: location.latitude,
        };
        setUserLocation(point);
        resolve(point);
      },
      fail: () => {
        resolve(null);
      },
    });
  });
}

function clearNativeRoute() {
  nativeRoutePoints.value = [];
  navigationRoute.value = null;
  simulatedNavigationMarker.value = null;
  stopSimulatedNavigation();
}

function renderNativeRoute(from: LngLat, destination: LngLat, routePoints?: LngLat[]) {
  clearNativeRoute();
  const points = routePoints && routePoints.length >= 2 ? routePoints : [from, destination];
  nativeRoutePoints.value = points.map((point) => ({
    longitude: point.lng,
    latitude: point.lat,
  }));
  simulatedNavigationMarker.value = points[0] || from;
  mapCenter.value = {
    lng: (from.lng + destination.lng) / 2,
    lat: (from.lat + destination.lat) / 2,
  };
}

function startSimulatedNavigation() {
  if (!navigationRoute.value || navigationRoute.value.points.length < 2) {
    uni.showToast({ title: "暂无可模拟的路线", icon: "none" });
    return;
  }

  stopSimulatedNavigation();
  navigationSimulationRunning.value = true;
  navigationSimulationIndex = 0;
  simulatedNavigationMarker.value = navigationRoute.value.points[0];
  navigationSimulationTimer = setInterval(() => {
    if (!navigationRoute.value) {
      stopSimulatedNavigation();
      return;
    }
    navigationSimulationIndex += 1;
    const point = navigationRoute.value.points[navigationSimulationIndex];
    if (!point) {
      stopSimulatedNavigation();
      uni.showToast({ title: "已到达目标点附近", icon: "none" });
      return;
    }
    simulatedNavigationMarker.value = point;
    setUserLocation(point);
  }, 1000);
}

function stopSimulatedNavigation() {
  if (navigationSimulationTimer) {
    clearInterval(navigationSimulationTimer);
    navigationSimulationTimer = null;
  }
  navigationSimulationRunning.value = false;
}

function mapSearchShellItemToMarker(item: MapShellItem): MapPointMarkerDto | null {
  if (item.lng === undefined || item.lat === undefined) {
    return null;
  }

  const isTask = item.type === "emergency_task" || item.type === "daily_task";
  const pointType = isTask ? "task" : item.type;
  const businessType =
    item.type === "emergency_task"
      ? "emergency"
      : item.type === "daily_task"
        ? "daily"
        : null;

  return {
    point_id: item.map_point_id || item.id,
    point_type: pointType,
    point_scope: "search_result",
    business_type: businessType,
    business_id: item.map_point_id || item.id,
    name: item.title,
    subtitle: item.subtitle,
    lng: item.lng,
    lat: item.lat,
    area_id: null,
    area_name: null,
    marker_key: item.icon_key || item.type,
    icon_key: item.icon_key || item.type,
    display_level: 80,
    visibility: "public",
    status: "active",
    cover_photo_url: item.cover_photo_url || null,
    preview_enabled: true,
    preview_min_zoom: 15,
    label_min_zoom: 16,
    distance_meters: item.distance_meters,
    extra: {
      source: "map_search",
      is_external_poi: !item.map_point_id,
    },
  };
}

function buildExternalSummaryFromItem(item: MapShellItem): MapPointSummaryResponse | null {
  if (!item.lng || !item.lat) {
    return null;
  }
  return {
    point_id: item.id,
    point_type: "landmark",
    business_type: "amap_poi",
    business_id: item.id,
    title: item.title,
    subtitle: item.subtitle,
    cover_photo_url: item.cover_photo_url || null,
    tags: ["地图点位"],
    description: item.description,
    location_name: item.title,
    location_detail: item.subtitle,
    route_instruction: null,
    landmark_hint: null,
    entrance_hint: null,
    lng: item.lng,
    lat: item.lat,
    distance_meters: item.distance_meters,
    photos: [],
    business_summary: {},
    actions: [
      {
        key: "navigate",
        label: "导航",
        enabled: true,
        disabled_reason: null,
        method: null,
        path: null,
        target_type: "page",
      },
    ],
  };
}

function buildExternalSummaryFromMarker(marker: MapPointMarkerDto): MapPointSummaryResponse {
  return {
    point_id: marker.point_id,
    point_type: "landmark",
    business_type: "amap_poi",
    business_id: marker.business_id,
    title: marker.name,
    subtitle: marker.subtitle,
    cover_photo_url: null,
    tags: ["地图点位"],
    description: marker.subtitle,
    location_name: marker.name,
    location_detail: marker.subtitle,
    route_instruction: null,
    landmark_hint: null,
    entrance_hint: null,
    lng: marker.lng,
    lat: marker.lat,
    distance_meters: marker.distance_meters,
    photos: [],
    business_summary: {},
    actions: [
      {
        key: "navigate",
        label: "导航",
        enabled: true,
        disabled_reason: null,
        method: null,
        path: null,
        target_type: "page",
      },
    ],
  };
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
  applyMapFilterOptions(data);
}

function applyMapFilterOptions(data: MapInitResponse) {
  filterOptions.value = normalizeMapFilterOptions(data.filter_options);
  if (
    activeFilter.value &&
    !filterOptions.value.some((option) => option.key === activeFilter.value)
  ) {
    activeFilter.value = null;
    mapPointMarkers.value = [];
  }
}

function getViewportQuery() {
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

  if (!activeFilter.value) {
    mapPointMarkers.value = [];
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    const data = await getMapPoints(token, {
      campus_id: campusMapConfig.value.id,
      ...getMapPointQueryByFilter(activeFilter.value, activeFilterOption.value),
      ...getViewportQuery(),
    });
    mapPointMarkers.value = data.items;
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
    const filterQuery = activeFilter.value
      ? getMapPointQueryByFilter(activeFilter.value, activeFilterOption.value)
      : {};
    const data = await searchMap(token, {
      keyword: normalizedKeyword,
      campus_id: campusMapConfig.value.id,
      point_types: filterQuery.point_types,
      include_external: true,
      user_lng: userLocation.value?.lng,
      user_lat: userLocation.value?.lat,
      page: 1,
      page_size: 20,
    });
    const items = data.items.map(mapSearchResultToShellItem).filter((item) => {
      return (
        !activeFilter.value ||
        activeFilter.value === ALL_MAP_FILTER_KEY ||
        isMapShellItemVisibleByFilter(item, activeFilter.value)
      );
    });
    searchResultItems.value = items;
    mapPointMarkers.value = items
      .map(mapSearchShellItemToMarker)
      .filter((marker): marker is MapPointMarkerDto => Boolean(marker));
    contentLoadState.value = "ready";
  } catch (error) {
    searchResultItems.value = [];
    mapPointMarkers.value = [];
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

  if (action.key === "edit_point") {
    if (!userStore.isAdmin) {
      uni.showToast({ title: "仅管理员可编辑点位", icon: "none" });
      return;
    }
    uni.navigateTo({
      url: action.path || `/pages/admin/map-point/edit?point_id=${selectedSummary.value.point_id}`,
    });
    return;
  }

  if (action.key === "view_detail") {
    if (action.target_type === "page" && action.path) {
      uni.navigateTo({ url: action.path });
      return;
    }

    if (selectedSummary.value.business_type === "feeding" && selectedSummary.value.business_id) {
      uni.navigateTo({
        url: `/pages/tasks/detail?task_id=${selectedSummary.value.business_id}`,
      });
      return;
    }
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
    const from = (await getCurrentLocationForNavigation()) || mapCenter.value;
    if (selectedSummary.value.business_type === "amap_poi") {
      renderInAppRoute(from, {
        point_id: selectedSummary.value.point_id,
        title: selectedSummary.value.title,
        destination: {
          lng: selectedSummary.value.lng,
          lat: selectedSummary.value.lat,
          location_name: selectedSummary.value.location_name || selectedSummary.value.title,
          amap_poi_id: null,
          amap_address: null,
        },
        route_instruction: selectedSummary.value.route_instruction,
        landmark_hint: selectedSummary.value.landmark_hint,
        entrance_hint: selectedSummary.value.entrance_hint,
        photos: [],
        amap_navigation: {
          mode: "walking",
          open_url: "",
          web_url: "",
        },
        route: {
          provider: "fallback",
          fallback: true,
          distance_meters: selectedSummary.value.distance_meters,
          duration_seconds: null,
          points: [from, { lng: selectedSummary.value.lng, lat: selectedSummary.value.lat }],
          steps: [],
        },
      });
      return;
    }
    const navigation = await getMapPointNavigation(token, selectedSummary.value.point_id, {
      from_lng: from.lng,
      from_lat: from.lat,
      mode: "walking",
    });
    renderInAppRoute(from, navigation);
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
    mapLoadState.value = "ready";
    await loadBottomContent();
    contentLoadState.value = "ready";
  } catch (error) {
    mapLoadState.value = "error";
    contentLoadState.value = "error";
    handleMapError(error, "地图初始化失败，请稍后重试。");
  }
}

async function refreshMapFilterOptions() {
  if (!isPageVisible.value || mapLoadState.value !== "ready") {
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  try {
    applyMapFilterOptions(await getMapInit(token));
  } catch (error) {
    handleMapError(error, "地图筛选加载失败");
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
  handleMapMarkerSelected(marker);
}

function handleMarkerLongPress(event: Event) {
  if (!userStore.isAdmin || !selectedSummary.value) {
    return;
  }
  if (selectedSummary.value.business_type === "amap_poi") {
    uni.showToast({ title: "外部地图点位不能编辑", icon: "none" });
    return;
  }
  const detail = (event as CustomEvent<{ longitude?: number; latitude?: number }>).detail;
  editedPointLocation.value = {
    lng: detail?.longitude ?? selectedSummary.value.lng,
    lat: detail?.latitude ?? selectedSummary.value.lat,
  };
  mapPointEditMode.value = true;
  uni.showToast({ title: "已进入点位编辑模式", icon: "none" });
}

function handleMapRegionChange(event: Event) {
  if (!mapPointEditMode.value) {
    return;
  }
  const detail = (event as CustomEvent<{
    type?: string;
    centerLocation?: { longitude?: number; latitude?: number };
  }>).detail;
  if (detail?.type && detail.type !== "end") {
    return;
  }
  const center = detail?.centerLocation;
  if (typeof center?.longitude === "number" && typeof center?.latitude === "number") {
    editedPointLocation.value = {
      lng: center.longitude,
      lat: center.latitude,
    };
  }
}

function handleMapMarkerSelected(marker: MapPointMarkerDto) {
  if (marker.point_scope === "search_result" && marker.extra.is_external_poi) {
    selectedSummary.value = buildExternalSummaryFromMarker(marker);
    return;
  }
  void loadPointSummary(marker.point_id);
}

function cancelMapPointEditMode() {
  mapPointEditMode.value = false;
  editedPointLocation.value = null;
}

async function saveEditedPointLocation() {
  if (!selectedSummary.value || !editedPointLocation.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  try {
    const updated = await updateAdminMapPointLocation(
      token,
      selectedSummary.value.point_id,
      editedPointLocation.value,
    );
    selectedSummary.value = {
      ...selectedSummary.value,
      lng: updated.lng,
      lat: updated.lat,
      location_name: updated.location_name,
      location_detail: updated.location_detail,
      route_instruction: updated.route_instruction,
      landmark_hint: updated.landmark_hint,
      entrance_hint: updated.entrance_hint,
    };
    mapPointMarkers.value = mapPointMarkers.value.map((marker) =>
      marker.point_id === updated.point_id
        ? { ...marker, lng: updated.lng, lat: updated.lat, name: updated.name }
        : marker,
    );
    mapCenter.value = { lng: updated.lng, lat: updated.lat };
    cancelMapPointEditMode();
    uni.showToast({ title: "点位位置已更新", icon: "none" });
  } catch (error) {
    handleMapError(error, "点位位置保存失败");
    uni.showToast({ title: contentErrorMessage.value, icon: "none" });
  }
}

function renderInAppRoute(
  from: LngLat,
  navigation: MapNavigationResponse,
) {
  const destination = {
    lng: navigation.destination.lng,
    lat: navigation.destination.lat,
  };
  const routePoints = navigation.route.points.length
    ? navigation.route.points
    : [from, destination];
  renderNativeRoute(from, destination, routePoints);
  navigationRoute.value = {
    title: navigation.title,
    distance_meters: navigation.route.distance_meters,
    duration_seconds: navigation.route.duration_seconds,
    points: routePoints,
    steps: navigation.route.steps,
  };
  uni.showToast({ title: "已在当前地图规划路线", icon: "none" });
}

function locateMe() {
  uni.getLocation({
    type: "gcj02",
    success: (location) => {
      const point = {
        lng: location.longitude,
        lat: location.latitude,
      };
      mapCenter.value = point;
      setUserLocation(point);
      void refreshMapPoints();
      uni.showToast({
        title: `已获取位置 ${location.latitude.toFixed(4)}`,
        icon: "none",
      });
    },
    fail: () => {
      centerMapToCampus();
      uni.showToast({ title: "无法获取当前位置", icon: "none" });
    },
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
    if (activeFilter.value) {
      void refreshMapPoints();
    } else {
      clearSearchResultMarkers();
    }
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
  void refreshMapFilterOptions().then(() => refreshMapPoints());
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

  clearNativeRoute();
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
  top: var(--catmap-page-title-top, 92rpx);
  left: var(--catmap-page-title-side, 42rpx);
  right: var(--catmap-page-title-side, 42rpx);
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.title-paw {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
}

.title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.map-viewport {
  position: absolute;
  z-index: 1;
  left: 24rpx;
  right: 24rpx;
  top: 218rpx;
  bottom: 664rpx;
  overflow: hidden;
  border-radius: 28rpx;
  background: rgba(228, 244, 218, 0.9);
  box-shadow: 0 14rpx 40rpx rgba(36, 75, 35, 0.12);

}

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

.map-filter-layer {
  position: absolute;
  z-index: 7;
  left: 52rpx;
  top: 300rpx;
  width: 360rpx;
  pointer-events: none;
}

.filter-panel-hit-layer {
  width: 244rpx;
  pointer-events: auto;
}

.filter-chip {
  position: relative;
  width: 224rpx;
  height: 78rpx;
  box-sizing: border-box;
  margin: 0;
  padding: 0 56rpx 0 20rpx;
  border: 0;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 30rpx rgba(20, 28, 40, 0.12);
  color: #161c28;
  display: flex;
  align-items: center;
  gap: 14rpx;
  line-height: 1;
  overflow: hidden;
}

.content-row::after,
.my-location-btn::after,
.clear-search::after,
.navigation-control::after,
.map-edit-button::after {
  border: 0;
}

.filter-chip-hover,
.map-button-hover,
.content-row-hover {
  opacity: 0.88;
  transform: translateY(2rpx);
}

.filter-chip-icon {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
}

.filter-label {
  min-width: 0;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-arrow-slot {
  position: absolute;
  top: 0;
  right: 18rpx;
  width: 34rpx;
  height: 78rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.filter-arrow-icon {
  width: 24rpx;
  height: 24rpx;
  transform: rotate(180deg);
  transform-origin: center center;
}

.filter-menu {
  width: 336rpx;
  box-sizing: border-box;
  margin-top: 14rpx;
  padding: 12rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 38rpx rgba(20, 28, 40, 0.13);
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  opacity: 0;
  transform: translateY(-8rpx) scaleY(0.96);
  transform-origin: top left;
  pointer-events: none;
}

.filter-option {
  height: 82rpx;
  box-sizing: border-box;
  margin: 0;
  padding: 14rpx 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #2a313d;
  line-height: 1.2;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.filter-option.is-active {
  background: #edf8e8;
  color: #267b2f;
}

.filter-option-icon {
  width: 42rpx;
  height: 42rpx;
}

.filter-option-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
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

.navigation-panel,
.map-edit-panel {
  position: absolute;
  z-index: 6;
  left: 24rpx;
  right: 154rpx;
  bottom: 32rpx;
  box-sizing: border-box;
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 34rpx rgba(20, 28, 40, 0.12);
}

.navigation-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 136rpx;
  align-items: center;
  gap: 16rpx;
}

.navigation-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.navigation-title,
.map-edit-title {
  color: #111827;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.15;
}

.navigation-meta,
.map-edit-desc {
  color: #6b7280;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1.35;
}

.navigation-control,
.map-edit-button {
  height: 58rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: #267b2f;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.navigation-control.is-secondary,
.map-edit-button.is-ghost {
  background: #edf8e8;
  color: #267b2f;
}

.map-edit-panel {
  bottom: 128rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.map-edit-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.content-drawer {
  position: absolute;
  z-index: 8;
  left: 24rpx;
  right: 24rpx;
  bottom: 150rpx;
  height: 460rpx;
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
  gap: 12rpx;
  line-height: 1;
  text-align: left;
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
