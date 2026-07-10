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
        <text class="title-text">喵图</text>
        <image class="title-paw" :src="pawIcon" mode="aspectFit" />
      </view>
      <text class="title-subtitle">探索校园 · 守护猫咪</text>
    </view>

    <view class="map-viewport">
      <map
        id="campus-map"
        class="native-map"
        :longitude="mapCenter.lng"
        :latitude="mapCenter.lat"
        :scale="mapScale"
        :markers="nativeMapMarkers"
        :polyline="nativeMapPolylines"
        :min-scale="campusMapConfig.min_zoom"
        :max-scale="campusMapConfig.max_zoom"
        :show-location="Boolean(userLocation)"
        :enable-poi="true"
        :enable-zoom="true"
        :enable-scroll="true"
        @tap="handleNativeMapTap"
        @markertap="handleNativeMarkerTap"
        @poitap="handleNativePoiTap"
        @markerlongpress="handleNativeMarkerLongPress"
        @longpress="handleMarkerLongPress"
        @regionchange="handleMapRegionChange"
      />

      <cover-view
        v-for="bubble in viewportMarkerBubbles"
        :key="bubble.key"
        class="marker-bubble"
        :style="bubble.style"
      >
        {{ bubble.title }}
      </cover-view>

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

      <cover-view
        v-if="mapPointEditMode"
        class="editable-marker-handle"
        :style="editableMarkerStyle"
        @touchmove.stop="dragEditedPoint"
        @touchend.stop="finishDraggingEditedPoint"
      >
        <cover-image class="editable-marker-icon" :src="locationIcon" />
      </cover-view>

      <view v-if="mapPointEditMode" class="map-edit-panel">
        <text class="map-edit-title">点位编辑模式</text>
        <text class="map-edit-desc">
          拖动地图上的点位，保存坐标：{{ editedPointLocationText }}
        </text>
        <view class="map-edit-actions">
          <button class="map-edit-button" @tap="saveEditedPointLocation">保存位置</button>
          <button class="map-edit-button is-ghost" @tap="cancelMapPointEditMode">
            取消
          </button>
        </view>
      </view>
    </view>

    <cover-view
      class="map-filter-layer"
      :class="{ 'map-filter-layer--preview-open': imagePreviewVisible }"
    >
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
        <cover-view v-if="filterMenuOpen" class="filter-menu">
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

      <view
        class="search-box"
        :class="{ 'is-focused': isSearchMode }"
        @tap="focusSearch"
        @touchstart="drawer.touchstart"
        @touchmove="drawer.touchmove"
        @touchend="drawer.touchend"
      >
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
          <view
            v-if="activeFilter === TASK_MAP_FILTER_KEY && !isSearchMode"
            class="section-title-trigger"
            @tap="selectTaskCompletionFilter"
          >
            <text class="section-title">{{ contentSectionTitle }}</text>
            <text class="section-title-arrow">∨</text>
          </view>
          <text v-else class="section-title">{{ contentSectionTitle }}</text>
          <text class="section-action">{{ contentSectionAction }}</text>
        </view>

        <view v-if="navigationRoute" class="navigation-route-card">
          <view class="navigation-route-head">
            <view>
              <text class="navigation-route-title">{{ navigationRoute.title }}</text>
              <text class="navigation-route-meta">
                {{ navigationRouteDistance }} · {{ navigationRouteDuration }}
              </text>
            </view>
            <button
              class="navigation-end-button"
              hover-class="summary-action-hover"
              @tap="clearNativeRoute"
            >
              结束
            </button>
          </view>
          <view class="navigation-route-steps">
            <text
              v-for="(step, index) in navigationRouteSteps"
              :key="index"
              class="navigation-route-step"
            >
              {{ navigationRouteStepText(step, index) }}
            </text>
          </view>
        </view>

        <view v-else-if="selectedSummary" class="summary-card">
          <view class="summary-card-head">
            <image
              v-if="summaryAvatarUrl"
              class="summary-avatar-image"
              :src="summaryAvatarUrl"
              mode="aspectFill"
              @tap="previewSummaryAvatar"
            />
            <view v-else class="summary-icon" :class="`item-icon-${summaryType}`">
              <text>{{ getItemSymbol(summaryType) }}</text>
            </view>
            <view class="summary-main">
              <view class="summary-title-row">
                <text class="summary-title">{{ selectedSummary.title }}</text>
                <text v-if="summaryTypeTag" class="summary-type-badge">
                  {{ summaryTypeTag }}
                </text>
              </view>
              <text class="summary-subtitle">{{ summarySubtitleText }}</text>
            </view>
          </view>
          <view v-if="summaryPreviewPhotos.length" class="summary-photo-strip">
            <view
              class="summary-photo-grid"
              :class="`count-${summaryPreviewPhotos.length}`"
            >
              <button
                v-for="photo in summaryPreviewPhotos"
                :key="photo.photo_id"
                class="summary-photo-cell"
                hover-class="summary-photo-hover"
                @tap="previewSummaryPhoto(photo)"
              >
                <image
                  class="summary-photo-thumb"
                  :src="getSummaryPhotoThumb(photo)"
                  mode="aspectFill"
                />
              </button>
            </view>
          </view>
          <text v-if="summaryDescriptionText" class="summary-desc">
            {{ summaryDescriptionText }}
          </text>
          <view v-if="summaryLocationText" class="summary-location">
            <text>{{ summaryLocationText }}</text>
          </view>
          <view v-if="showSummaryPoi" class="summary-poi">
            <text v-if="summaryPoiTitleText" class="summary-poi-title">{{ summaryPoiTitleText }}</text>
            <text v-if="summaryPoiDescriptionText" class="summary-poi-desc">
              {{ summaryPoiDescriptionText }}
            </text>
          </view>
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
            <image
              v-if="item.cover_photo_url"
              class="item-cover"
              :src="item.cover_photo_url"
              mode="aspectFill"
            />
            <view v-else class="item-icon" :class="`item-icon-${item.type}`">
              <text>{{ getItemSymbol(item.type) }}</text>
            </view>
            <view class="item-main">
              <text class="item-title">{{ item.title }}</text>
              <view class="item-meta">
                <text>{{ getShellItemMetaText(item) }}</text>
              </view>
            </view>
            <text class="item-status" :class="`status-${getShellItemStatusTone(item)}`">
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
    <ImagePreviewModal
      :visible="imagePreviewVisible"
      :images="imagePreviewUrls"
      :current-index="imagePreviewIndex"
      @change="setImagePreviewIndex"
      @close="closeImagePreview"
    />
  </view>
</template>

<script module="drawer" lang="wxs" src="./drawer.wxs"></script>
<script module="filterMenu" lang="wxs" src="./filter-menu.wxs"></script>

<script setup lang="ts">
import { onHide, onShow } from "@dcloudio/uni-app";
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";

import {
  getMapBottomContent,
  getMapInit,
  getMapPointNavigation,
  getMapPointSummary,
  getMapPoints,
  getWalkingRoute,
  resolveMapPoi,
  searchMap,
  type CardActionDto,
  type MapInitResponse,
  type MapNavigationResponse,
  type MapPointMarkerDto,
  type MapPointPhotoDto,
  type MapPointSummaryResponse,
} from "@/api/map";
import { updateAdminMapPointLocation } from "@/api/admin-map";
import AppTabBar from "@/components/AppTabBar.vue";
import ImagePreviewModal from "@/components/ImagePreviewModal.vue";
import { ApiBusinessError, isRequestCanceledError } from "@/services/request";
import {
  getCachedUserLocation,
  preloadUserLocation,
  subscribeUserLocation,
} from "@/services/user-location";
import { useUserStore } from "@/stores/user";

import allMarkerPointIcon from "../../../素材/png/地图点/全部.png";
import catPointMarkerIcon from "../../../素材/png/地图点/猫咪点.png";
import dailyTaskPointIcon from "../../../素材/png/地图点/日常任务.png";
import dailyTaskPendingPointIcon from "../../../素材/png/地图点/日常任务红.png";
import emergencyTaskPointIcon from "../../../素材/png/地图点/紧急任务.png";
import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import filterDefaultIcon from "../../../素材/png/地图点/筛选.png";
import landmarkPointIcon from "../../../素材/png/地图点/地标.png";
import supplyPointMarkerIcon from "../../../素材/png/地图点/物资点.png";
import locationIcon from "../../../素材/png/菜单/定位.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";
import {
  ALL_MAP_FILTER_KEY,
  DEFAULT_MAP_TASK_COMPLETION_FILTER,
  HBNU_CAMPUS,
  HBNU_CAMPUS_CORE_BOUNDS,
  MAP_PENDING_NAVIGATION_STORAGE_KEY,
  NO_MAP_FILTER_KEY,
  NO_MAP_FILTER_LABEL,
  NO_MAP_FILTER_OPTION,
  clampLngLatToBounds,
  expandLngLatBounds,
  filterMapShellItemsByTaskCompletion,
  formatDistance,
  getMarkerBubbleVisibility,
  getMarkerDisplayMode,
  getMapFocusTargetScale,
  getMapFilterLabel,
  getMapPointQueryByFilter,
  isFiniteLngLat,
  isFiniteLngLatBounds,
  isLngLatInsideBounds,
  isLngLatInsideViewport,
  isMapShellItemVisibleByFilter,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  normalizeMapFilterOptions,
  shouldQueryMapScaleFromRegionChange,
  shouldSyncMapScaleFromRegionChange,
  TASK_MAP_FILTER_KEY,
  type MapFilterOption,
  resolveMapShellItemType,
  type MapFilterKey,
  type MapMarkerDisplayMode,
  type CampusMapConfig,
  type LngLat,
  type MapViewportBounds,
  type MapShellItem,
  type MapShellItemType,
  type MapTaskCompletionFilter,
  toNativeMapPoint,
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

interface PendingMapNavigation {
  source?: string;
  task_id?: string;
  map_point_id?: string | null;
  shell_item?: MapShellItem;
  poi?: MapPointSummaryResponse["associated_poi"];
}

type NativeRoutePoint = { longitude: number; latitude: number };
type NativeRegionChangeDetail = {
  type?: string;
  causedBy?: string;
  scale?: number;
  centerLocation?: { longitude?: number; latitude?: number };
};

interface ViewportMarkerBubble {
  key: string;
  title: string;
  style: string;
}

interface NativeMapMarker {
  id: number;
  longitude: number;
  latitude: number;
  iconPath: string;
  width: number;
  height: number;
  anchor?: { x: number; y: number };
  callout?: {
    content: string;
    color: string;
    fontSize: number;
    borderRadius: number;
    bgColor: string;
    padding: number;
    display: "BYCLICK" | "ALWAYS";
    textAlign?: "left" | "right" | "center";
  };
}

type NativeMapContext = {
  moveToLocation?: (options: {
    longitude: number;
    latitude: number;
    success?: () => void;
    fail?: () => void;
  }) => void;
  includePoints?: (options: {
    points: NativeRoutePoint[];
    padding?: number[];
    success?: () => void;
    fail?: () => void;
  }) => void;
  getScale?: (options: {
    success?: (result: { scale?: number }) => void;
    fail?: () => void;
    complete?: () => void;
  }) => void;
  getRegion?: (options: {
    success?: (result: {
      southwest?: { longitude?: number; latitude?: number };
      northeast?: { longitude?: number; latitude?: number };
    }) => void;
    fail?: () => void;
    complete?: () => void;
  }) => void;
  toScreenLocation?: (options: {
    longitude: number;
    latitude: number;
    success?: (result: { x?: number; y?: number }) => void;
    fail?: () => void;
    complete?: () => void;
  }) => void;
};

const userStore = useUserStore();
const sysInfo = uni.getSystemInfoSync();
const drawerConfig = ref({
  rpxRatio: sysInfo.windowWidth / 750,
  windowHeight: sysInfo.windowHeight,
});
const filterMenuOpen = ref(false);
const filterOptions = ref<MapFilterOption[]>([NO_MAP_FILTER_OPTION]);
const activeFilter = ref<MapFilterKey | null>(null);
const taskCompletionFilter = ref<MapTaskCompletionFilter>(DEFAULT_MAP_TASK_COMPLETION_FILTER);
const searchKeyword = ref("");
const mapLoadState = ref<MapLoadState>("idle");
const contentLoadState = ref<ContentLoadState>("idle");
const contentErrorMessage = ref("");
const campusMapConfig = ref<CampusMapConfig>(HBNU_CAMPUS);
const mapCenter = ref<LngLat>({ ...HBNU_CAMPUS.center });
const mapScale = ref(HBNU_CAMPUS.default_zoom);
const observedMapScale = ref(HBNU_CAMPUS.default_zoom);
const userLocation = ref<LngLat | null>(null);
const mapPointMarkers = ref<MapPointMarkerDto[]>([]);
const nativeRoutePoints = ref<NativeRoutePoint[]>([]);
const navigationRoute = ref<NavigationRouteState | null>(null);
const bottomContentItems = ref<MapShellItem[]>([]);
const searchResultItems = ref<MapShellItem[]>([]);
const selectedSummary = ref<MapPointSummaryResponse | null>(null);
const imagePreviewVisible = ref(false);
const imagePreviewUrls = ref<string[]>([]);
const imagePreviewIndex = ref(0);
const selectedPoiMarker = ref<MapPointMarkerDto | null>(null);
const nativeMarkerLookup = shallowRef(new Map<number, MapPointMarkerDto>());
const pendingPointSummaryRequestId = ref<number | null>(null);
const pendingPoiResolveKey = ref<string | null>(null);
const lastResolvedPoiTapKey = ref<string | null>(null);
const nativePoiTapSuppressedUntil = ref(0);
const lastPointTapAt = ref(0);
const mapPointFilterReady = ref(false);
const viewportMarkerBubbles = ref<ViewportMarkerBubble[]>([]);
const drawerResizeInProgress = ref(false);
const mapPointEditMode = ref(false);
const editedPointLocation = ref<LngLat | null>(null);
const editableMarkerScreenPosition = ref<{ x: number; y: number } | null>(null);
const MAP_FILTER_ICON_SRC: Record<string, string> = {
  none: filterDefaultIcon,
  all: allMarkerPointIcon,
  emergency_task: emergencyTaskPointIcon,
  daily_task: dailyTaskPointIcon,
  cat: catPointMarkerIcon,
  supply: supplyPointMarkerIcon,
  landmark: landmarkPointIcon,
  feeding_pending: dailyTaskPendingPointIcon,
  feeding_completed: dailyTaskPointIcon,
  task: dailyTaskPendingPointIcon,
  filter_none: filterDefaultIcon,
};
const MARKER_LONG_PRESS_HIT_METERS = 60;
const NATIVE_MARKER_HIT_SIZE = 34;
const MAP_BLANK_TAP_GUARD_MS = 250;
const DRAWER_RESIZE_SETTLE_MS = 520;
const MAP_FOCUS_SETTLE_MS = 720;
const MAP_CENTER_SYNC_EPSILON_METERS = 0.75;
const MAP_SCALE_SYNC_EPSILON = 0.01;
const MAP_POINT_FOCUS_SCALE = 18;

let searchTimer: ReturnType<typeof setTimeout> | null = null;
let mapRefreshTimer: ReturnType<typeof setTimeout> | null = null;
let drawerResizeResumeTimer: ReturnType<typeof setTimeout> | null = null;
let unsubscribeUserLocation: (() => void) | null = null;
let pointSummaryRequestSeq = 0;
let poiResolveRequestSeq = 0;
let viewportMarkerBubbleRequestSeq = 0;
let mapCenterMoveRequestId = 0;
let viewportMarkerBubblesVisible = false;

const isPageVisible = ref(true);
const isSearchMode = computed(() => searchKeyword.value.trim().length > 0);
const taskCompletionFilterLabel = computed(() => {
  if (taskCompletionFilter.value === "all") {
    return "全部任务";
  }
  if (taskCompletionFilter.value === "completed") {
    return "已完成任务";
  }
  return "未完成任务";
});
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
const filteredTaskMapPointMarkers = computed(() => {
  if (activeFilter.value !== TASK_MAP_FILTER_KEY || isSearchMode.value) {
    return mapPointMarkers.value;
  }

  return mapPointMarkers.value.filter(
    (marker) =>
      filterMapShellItemsByTaskCompletion(
        [mapMarkerToShellItem(marker)],
        taskCompletionFilter.value,
      ).length > 0,
  );
});
const visibleItems = computed(() => {
  const items = isSearchMode.value
    ? searchResultItems.value
    : bottomContentItems.value;
  const taskCompletionItems =
    activeFilter.value === TASK_MAP_FILTER_KEY && !isSearchMode.value
      ? filterMapShellItemsByTaskCompletion(items, taskCompletionFilter.value)
      : items;

  return taskCompletionItems.filter((item) => {
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
function getSummaryPhotoThumb(photo: MapPointPhotoDto): string {
  return photo.thumbnail_url || photo.file_url;
}

function getSummaryPhotoFullUrl(photo: MapPointPhotoDto): string {
  return photo.file_url || photo.thumbnail_url || "";
}

const summaryPhotos = computed(() =>
  (selectedSummary.value?.photos || []).filter((photo) => getSummaryPhotoThumb(photo)),
);
const summaryAvatarUrl = computed(() => {
  const firstPhoto = summaryPhotos.value[0];
  return firstPhoto
    ? getSummaryPhotoThumb(firstPhoto)
    : selectedSummary.value?.cover_photo_url || "";
});
const summaryPreviewPhotos = computed(() => summaryPhotos.value.slice(1, 4));
const summaryPreviewUrls = computed(() => {
  const urls = summaryPhotos.value
    .map((photo) => getSummaryPhotoFullUrl(photo))
    .filter((url) => url);
  return urls.length || !summaryAvatarUrl.value ? urls : [summaryAvatarUrl.value];
});
function getSummaryPointTypeLabel(
  pointType: string,
  businessType: string | null | undefined,
): string {
  if (pointType === "task") {
    if (businessType === "emergency") {
      return "紧急任务";
    }
    if (businessType === "feeding") {
      return "投喂任务";
    }
    return "日常任务";
  }

  const labels: Record<string, string> = {
    cat: "猫咪点",
    supply: "物资点",
    landmark: "地标",
  };

  return labels[pointType] || getMapFilterLabel(resolveMapShellItemType(pointType, businessType));
}

const summaryPointTypeLabel = computed(() => {
  const summary = selectedSummary.value;
  return summary ? getSummaryPointTypeLabel(summary.point_type, summary.business_type) : "";
});
const summaryTypeTag = computed(() => summaryPointTypeLabel.value);
const summaryActions = computed<CardActionDto[]>(() => {
  if (!selectedSummary.value) {
    return [];
  }
  return selectedSummary.value.actions;
});
const associatedPoi = computed(() => selectedSummary.value?.associated_poi || null);
function normalizeSummaryText(value: string | null | undefined): string {
  return (value || "")
    .trim()
    .replace(/\s+/g, "")
    .replace(/[·:：,，。.;；-]/g, "")
    .toLowerCase();
}

function isDuplicateSummaryText(
  value: string | null | undefined,
  candidates: Array<string | null | undefined>,
): boolean {
  const normalized = normalizeSummaryText(value);
  if (!normalized) {
    return true;
  }

  return candidates.some((candidate) => {
    const normalizedCandidate = normalizeSummaryText(candidate);
    return (
      normalizedCandidate.length > 0 &&
      (normalizedCandidate === normalized ||
        normalizedCandidate.includes(normalized) ||
        normalized.includes(normalizedCandidate))
    );
  });
}

function firstDistinctSummaryText(
  values: Array<string | null | undefined>,
  candidates: Array<string | null | undefined>,
): string {
  for (const value of values) {
    const text = value?.trim();
    if (text && !isDuplicateSummaryText(text, candidates)) {
      return text;
    }
  }
  return "";
}

const summarySubtitleText = computed(() => {
  const summary = selectedSummary.value;
  if (!summary) {
    return "";
  }

  return (
    firstDistinctSummaryText(
      [summary.subtitle, summary.location_name, summary.location_detail],
      [summary.title],
    ) || "校园点位"
  );
});
const summaryDescriptionText = computed(() => {
  const summary = selectedSummary.value;
  if (!summary) {
    return "";
  }
  const poi = associatedPoi.value;
  return firstDistinctSummaryText(
    [summary.description],
    [
      summary.title,
      summarySubtitleText.value,
      summary.location_name,
      summary.location_detail,
      poi?.name,
      poi?.category,
      poi?.address,
    ],
  );
});
const summaryLocationText = computed(() => {
  const summary = selectedSummary.value;
  if (!summary) {
    return "";
  }
  const parts: string[] = [];
  const locationText = firstDistinctSummaryText(
    [summary.location_name, summary.location_detail],
    [summary.title, summarySubtitleText.value, summaryDescriptionText.value],
  );
  if (locationText) {
    parts.push(locationText);
  }
  if (summary.distance_meters !== null) {
    parts.push(`距离 ${formatDistance(summary.distance_meters)}`);
  }
  return parts.join(" · ");
});
const summaryPoiTitleText = computed(() => {
  const summary = selectedSummary.value;
  const poi = associatedPoi.value;
  if (!summary || !poi) {
    return "";
  }
  const poiName = firstDistinctSummaryText(
    [poi.name],
    [summary.title, summary.location_name, summary.location_detail],
  );
  return poiName ? `公共地点：${poiName}` : "";
});
const summaryPoiDescriptionText = computed(() => {
  const summary = selectedSummary.value;
  const poi = associatedPoi.value;
  if (!summary || !poi) {
    return "";
  }
  const parts: string[] = [];
  const category = firstDistinctSummaryText(
    [poi.category],
    [summary.title, summarySubtitleText.value, summaryDescriptionText.value],
  );
  if (category) {
    parts.push(category);
  }
  const address = firstDistinctSummaryText(
    [poi.address],
    [
      summary.title,
      summarySubtitleText.value,
      summaryDescriptionText.value,
      summary.location_name,
      ...parts,
    ],
  );
  if (address) {
    parts.push(address);
  }
  return parts.join(" · ");
});
const showSummaryPoi = computed(() =>
  Boolean(associatedPoi.value && (summaryPoiTitleText.value || summaryPoiDescriptionText.value)),
);

function previewSummaryPhoto(photo: MapPointPhotoDto) {
  const current = getSummaryPhotoFullUrl(photo);
  if (!current) {
    return;
  }
  openImagePreview(summaryPreviewUrls.value, current);
}

function previewSummaryAvatar() {
  const firstPhoto = summaryPhotos.value[0];
  const current = firstPhoto ? getSummaryPhotoFullUrl(firstPhoto) : summaryAvatarUrl.value;
  if (!current) {
    return;
  }
  openImagePreview(summaryPreviewUrls.value, current);
}

function openImagePreview(urls: string[], current: string) {
  const uniqueUrls = Array.from(new Set(urls.filter((url) => url)));
  const resolvedUrls = uniqueUrls.length ? uniqueUrls : [current];
  const currentIndex = Math.max(0, resolvedUrls.indexOf(current));
  filterMenuOpen.value = false;
  imagePreviewUrls.value = resolvedUrls;
  imagePreviewIndex.value = currentIndex;
  imagePreviewVisible.value = true;
}

function closeImagePreview() {
  imagePreviewVisible.value = false;
}

function setImagePreviewIndex(index: number) {
  imagePreviewIndex.value = index;
}

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
const navigationRouteSteps = computed<NavigationRouteState["steps"]>(() => {
  const steps = navigationRoute.value?.steps || [];
  const visibleSteps = steps.filter((step) => step.instruction.trim());
  return visibleSteps.length
    ? visibleSteps
    : [
        {
          instruction: "路线已规划，可在地图上查看绿色路线。",
          distance_meters: 0,
          duration_seconds: 0,
          points: [],
        },
      ];
});
function navigationRouteStepText(
  step: NavigationRouteState["steps"][number],
  index: number,
): string {
  return `${index + 1}、${step.instruction.trim() || "继续前行"}`;
}
const editedPointLocationText = computed(() => {
  const point = editedPointLocation.value || selectedSummary.value;
  if (!point) {
    return "未知坐标";
  }
  return `${point.lng.toFixed(6)}, ${point.lat.toFixed(6)}`;
});
const editableMarkerStyle = computed(() => {
  const position = editableMarkerScreenPosition.value;
  if (!position) {
    return "left: 50%; top: 50%;";
  }
  return `left: ${position.x}px; top: ${position.y}px;`;
});
const contentSectionTitle = computed(() => {
  if (navigationRoute.value) {
    return "路线导航";
  }

  if (selectedSummary.value) {
    return "点位详情";
  }

  if (isSearchMode.value) {
    return "搜索结果";
  }

  if (activeFilter.value) {
    if (activeFilter.value === TASK_MAP_FILTER_KEY) {
      return taskCompletionFilterLabel.value;
    }
    return activeFilterLabel.value;
  }

  return "最新任务";
});
const contentSectionAction = computed(() => {
  if (navigationRoute.value) {
    return `${navigationRouteDistance.value} · ${navigationRouteDuration.value}`;
  }

  if (selectedSummary.value) {
    return "";
  }

  if (contentLoadState.value === "loading") {
    return "加载中";
  }

  if (isSearchMode.value) {
    return `${visibleItems.value.length} 个结果`;
  }

  if (activeFilter.value) {
    return `${visibleItems.value.length} 个点位`;
  }

  return "";
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
function isExternalPoiMarker(marker: MapPointMarkerDto): boolean {
  return marker.business_type === "tencent_poi" || marker.extra.is_external_poi === true;
}

function isSamePoiMarker(a: MapPointMarkerDto, b: MapPointMarkerDto): boolean {
  return (
    a.point_id === b.point_id ||
    (isExternalPoiMarker(a) &&
      isExternalPoiMarker(b) &&
      Math.abs(a.lng - b.lng) < 0.000001 &&
      Math.abs(a.lat - b.lat) < 0.000001)
  );
}

function getPoiTapKey(input: { lng: number; lat: number; keyword?: string }): string {
  const lng = input.lng.toFixed(5);
  const lat = input.lat.toFixed(5);
  const keyword = (input.keyword || "").trim().toLowerCase();
  return `${lng},${lat}:${keyword}`;
}

function isSameSelectedPoiTap(input: { lng: number; lat: number; keyword?: string }): boolean {
  const summary = selectedSummary.value;
  if (summary?.business_type !== "tencent_poi") {
    return false;
  }

  const tappedPoint = { lng: input.lng, lat: input.lat };
  const selectedPoint = { lng: summary.lng, lat: summary.lat };
  const keyword = (input.keyword || "").trim();
  const titleMatched = keyword ? summary.title === keyword || summary.location_name === keyword : true;
  const distance = distanceMetersBetween(tappedPoint, selectedPoint);
  return distance <= 8 || (titleMatched && distance <= 30);
}

function shouldSkipPoiResolve(
  poiTapKey: string,
  input?: { lng: number; lat: number; keyword?: string },
): boolean {
  if (pendingPoiResolveKey.value !== null) {
    return true;
  }
  if (input && isSameSelectedPoiTap(input)) {
    return true;
  }

  return (
    lastResolvedPoiTapKey.value === poiTapKey &&
    selectedSummary.value?.business_type === "tencent_poi" &&
    selectedPoiMarker.value !== null
  );
}

function suppressNativePoiTaps(durationMs = MAP_FOCUS_SETTLE_MS) {
  nativePoiTapSuppressedUntil.value = Date.now() + durationMs;
}

function isNativePoiTapSuppressed(): boolean {
  return Date.now() < nativePoiTapSuppressedUntil.value;
}

function startPointSummaryRequest(): number {
  pointSummaryRequestSeq += 1;
  pendingPointSummaryRequestId.value = pointSummaryRequestSeq;
  return pointSummaryRequestSeq;
}

function isCurrentPointSummaryRequest(requestId: number): boolean {
  return (
    requestId === pointSummaryRequestSeq &&
    pendingPointSummaryRequestId.value === requestId
  );
}

function cancelPointSummaryRequest() {
  pointSummaryRequestSeq += 1;
  pendingPointSummaryRequestId.value = null;
}

function finishPointSummaryRequest(requestId: number) {
  if (pendingPointSummaryRequestId.value === requestId) {
    pendingPointSummaryRequestId.value = null;
  }
}

function startPoiResolve(poiTapKey: string): number {
  cancelPointSummaryRequest();
  poiResolveRequestSeq += 1;
  pendingPoiResolveKey.value = poiTapKey;
  return poiResolveRequestSeq;
}

function isCurrentPoiResolve(resolveRequestId: number): boolean {
  return resolveRequestId === poiResolveRequestSeq;
}

function finishPoiResolve(resolveRequestId: number, poiTapKey: string) {
  if (isCurrentPoiResolve(resolveRequestId) && pendingPoiResolveKey.value === poiTapKey) {
    pendingPoiResolveKey.value = null;
  }
}

function clearNativePoiSelection() {
  poiResolveRequestSeq += 1;
  pendingPoiResolveKey.value = null;
  lastResolvedPoiTapKey.value = null;
  selectedPoiMarker.value = null;
  if (selectedSummary.value?.business_type === "tencent_poi") {
    selectedSummary.value = null;
  }
}

function markPointTapInteraction() {
  lastPointTapAt.value = Date.now();
}

function shouldIgnoreNativeMapTap(): boolean {
  return Date.now() - lastPointTapAt.value < MAP_BLANK_TAP_GUARD_MS;
}

function setDrawerResizeInProgress(active: boolean) {
  if (drawerResizeResumeTimer) {
    clearTimeout(drawerResizeResumeTimer);
    drawerResizeResumeTimer = null;
  }

  if (active) {
    drawerResizeInProgress.value = true;
    return;
  }

  drawerResizeResumeTimer = setTimeout(() => {
    drawerResizeInProgress.value = false;
    drawerResizeResumeTimer = null;
    syncMapScaleFromContext();
  }, DRAWER_RESIZE_SETTLE_MS);
}

defineExpose({
  setDrawerResizeInProgress,
});

function clearSelectedMapPointState() {
  const hadPendingPointSummary = pendingPointSummaryRequestId.value !== null;
  cancelPointSummaryRequest();
  filterMenuOpen.value = false;
  poiResolveRequestSeq += 1;
  pendingPoiResolveKey.value = null;
  lastResolvedPoiTapKey.value = null;
  selectedSummary.value = null;
  selectedPoiMarker.value = null;
  if (hadPendingPointSummary && contentLoadState.value === "loading") {
    contentLoadState.value = "ready";
  }
}

function getNativeMarkerDisplayMode(marker: MapPointMarkerDto): MapMarkerDisplayMode {
  if (isExternalPoiMarker(marker)) {
    return "icon";
  }

  const selectedPointId = selectedSummary.value?.point_id;
  if (selectedPointId && selectedPointId !== marker.point_id) return "icon";

  return getMarkerDisplayMode({
    selected: selectedPointId === marker.point_id,
    zoom: observedMapScale.value,
    visibleMarkerCount: nativeMarkerSourceMarkers.value.length,
  });
}

const nativeMarkerSourceMarkers = computed(() => {
  const markers = filteredTaskMapPointMarkers.value.filter((marker) =>
    isFiniteLngLat({ lng: marker.lng, lat: marker.lat }),
  );
  const selectedPoi = selectedPoiMarker.value;

  if (
    selectedPoi &&
    isFiniteLngLat({ lng: selectedPoi.lng, lat: selectedPoi.lat }) &&
    !markers.some((marker) => isSamePoiMarker(marker, selectedPoi))
  ) {
    markers.push(selectedPoi);
  }

  return markers;
});

function getMapViewportBounds(
  region: {
    southwest?: { longitude?: number; latitude?: number };
    northeast?: { longitude?: number; latitude?: number };
  },
): MapViewportBounds | null {
  const southwest = region.southwest;
  const northeast = region.northeast;
  if (
    typeof southwest?.longitude !== "number" ||
    typeof southwest?.latitude !== "number" ||
    typeof northeast?.longitude !== "number" ||
    typeof northeast?.latitude !== "number"
  ) {
    return null;
  }

  const bounds: MapViewportBounds = {
    southwest: { lng: southwest.longitude, lat: southwest.latitude },
    northeast: { lng: northeast.longitude, lat: northeast.latitude },
  };
  return isFiniteLngLatBounds({
    south_west: bounds.southwest,
    north_east: bounds.northeast,
  })
    ? bounds
    : null;
}

function isViewportBusinessMarker(marker: MapPointMarkerDto): boolean {
  return !isExternalPoiMarker(marker) && isFiniteLngLat({ lng: marker.lng, lat: marker.lat });
}

function getViewportMarkerBubbleKey(marker: MapPointMarkerDto): string {
  return `${marker.point_id || marker.business_id || marker.name}:${marker.lng.toFixed(6)},${marker.lat.toFixed(6)}`;
}

function clearViewportMarkerBubbles(resetVisibility = true) {
  viewportMarkerBubbleRequestSeq += 1;
  viewportMarkerBubbles.value = [];
  if (resetVisibility) {
    viewportMarkerBubblesVisible = false;
  }
}

function toViewportMarkerBubble(
  mapContext: NativeMapContext,
  marker: MapPointMarkerDto,
): Promise<ViewportMarkerBubble | null> {
  return new Promise((resolve) => {
    if (typeof mapContext.toScreenLocation !== "function") {
      resolve(null);
      return;
    }
    mapContext.toScreenLocation({
      longitude: marker.lng,
      latitude: marker.lat,
      success: (position) => {
        if (!Number.isFinite(position.x) || !Number.isFinite(position.y)) {
          resolve(null);
          return;
        }
        resolve({
          key: getViewportMarkerBubbleKey(marker),
          title: marker.name,
          style: `left: ${position.x}px; top: ${position.y}px;`,
        });
      },
      fail: () => resolve(null),
    });
  });
}

function refreshViewportMarkerBubbles() {
  const requestId = viewportMarkerBubbleRequestSeq + 1;
  viewportMarkerBubbleRequestSeq = requestId;
  viewportMarkerBubbles.value = [];
  if (
    drawerResizeInProgress.value ||
    !mapPointFilterReady.value ||
    !activeFilter.value ||
    !isPageVisible.value
  ) {
    viewportMarkerBubblesVisible = false;
    return;
  }

  const mapContext = uni.createMapContext("campus-map") as unknown as NativeMapContext;
  if (typeof mapContext.getRegion !== "function") {
    viewportMarkerBubblesVisible = false;
    return;
  }

  mapContext.getRegion({
    success: (region) => {
      if (requestId !== viewportMarkerBubbleRequestSeq) {
        return;
      }
      const bounds = getMapViewportBounds(region);
      if (!bounds) {
        viewportMarkerBubblesVisible = false;
        return;
      }
      const visibleMarkers = nativeMarkerSourceMarkers.value
        .filter(isViewportBusinessMarker)
        .filter((marker) => isLngLatInsideViewport(marker, bounds));
      const visibleBubbleMarkers = visibleMarkers.filter(
        (marker) => marker.point_id !== selectedSummary.value?.point_id,
      );
      const shouldShow = getMarkerBubbleVisibility({
        zoom: observedMapScale.value,
        stable: true,
        filterReady: mapPointFilterReady.value,
        hasActiveMarkerFilter: Boolean(activeFilter.value),
        visibleMarkerCount: visibleMarkers.length,
        previousVisible: viewportMarkerBubblesVisible,
      });
      viewportMarkerBubblesVisible = shouldShow;
      if (!shouldShow || typeof mapContext.toScreenLocation !== "function") {
        return;
      }

      void Promise.all(
        visibleBubbleMarkers
          .slice(0, 6)
          .map((marker) => toViewportMarkerBubble(mapContext, marker)),
      ).then((bubbles) => {
        if (requestId !== viewportMarkerBubbleRequestSeq) {
          return;
        }
        viewportMarkerBubbles.value = bubbles.filter(
          (bubble): bubble is ViewportMarkerBubble => Boolean(bubble),
        );
      });
    },
    fail: () => {
      if (requestId === viewportMarkerBubbleRequestSeq) {
        viewportMarkerBubblesVisible = false;
      }
    },
  });
}

function hashNativeMarkerKey(key: string): number {
  let hash = 0;
  for (let index = 0; index < key.length; index += 1) {
    hash = (hash * 31 + key.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function getNativeMarkerStableId(marker: MapPointMarkerDto): number {
  const key =
    marker.point_id ||
    marker.business_id ||
    `${marker.point_type}:${marker.business_type}:${marker.lng.toFixed(6)},${marker.lat.toFixed(6)}:${marker.name}`;
  return 1000 + (hashNativeMarkerKey(key) % 800000);
}

function findNativeMarkerByStableId(markerId: number): MapPointMarkerDto | null {
  return nativeMarkerLookup.value.get(markerId) || null;
}

function buildNativeMarkerTitleCallout(title: string): NonNullable<NativeMapMarker["callout"]> {
  if (!title.trim()) {
    return {
      content: "",
      color: "#111827",
      fontSize: 1,
      borderRadius: 0,
      bgColor: "#ffffff",
      padding: 0,
      display: "BYCLICK",
      textAlign: "center",
    };
  }

  return {
    content: title,
    color: "#111827",
    fontSize: 12,
    borderRadius: 8,
    bgColor: "#ffffff",
    padding: 8,
    display: "ALWAYS",
    textAlign: "center",
  };
}

const nativeMapMarkers = computed(() => {
  const usedMarkerIds = new Set<number>();
  const markerLookup = new Map<number, MapPointMarkerDto>();
  const markers: NativeMapMarker[] = nativeMarkerSourceMarkers.value.map((marker) => {
    const type = resolveMapShellItemType(marker.point_type, marker.business_type);
    const displayMode = getNativeMarkerDisplayMode(marker);
    let markerId = getNativeMarkerStableId(marker);
    while (usedMarkerIds.has(markerId)) {
      markerId += 1;
    }
    usedMarkerIds.add(markerId);
    markerLookup.set(markerId, marker);

    return {
      id: markerId,
      longitude: marker.lng,
      latitude: marker.lat,
      iconPath: getNativeMarkerIcon(type, marker),
      width: NATIVE_MARKER_HIT_SIZE,
      height: NATIVE_MARKER_HIT_SIZE,
      anchor: { x: 0.5, y: 1 },
      callout:
        displayMode === "label"
          ? buildNativeMarkerTitleCallout(marker.name)
          : buildNativeMarkerTitleCallout(""),
    };
  });
  if (mapPointEditMode.value && editedPointLocation.value) {
    markers.push({
      id: 900002,
      longitude: editedPointLocation.value.lng,
      latitude: editedPointLocation.value.lat,
      iconPath: locationIcon,
      width: 38,
      height: 38,
      anchor: { x: 0.5, y: 1 },
      callout: {
        content: "编辑位置",
        color: "#111827",
        fontSize: 12,
        borderRadius: 8,
        bgColor: "#ffffff",
        padding: 8,
        display: "BYCLICK",
      },
    });
  }
  nativeMarkerLookup.value = markerLookup;
  return markers;
});
const nativeMapPolylines = computed(() => {
  if (nativeRoutePoints.value.length < 2) {
    return [];
  }

  return [
    {
      points: nativeRoutePoints.value,
      color: "#267b2f",
      width: 8,
      dottedLine: false,
      arrowLine: true,
      borderColor: "#ffffff",
      borderWidth: 2,
    },
  ];
});
function selectFilter(option: MapFilterOption) {
  cancelPointSummaryRequest();
  filterMenuOpen.value = false;
  selectedSummary.value = null;
  selectedPoiMarker.value = null;
  clearViewportMarkerBubbles();
  const nextFilter = option.key === NO_MAP_FILTER_KEY ? null : option.key;
  if (nextFilter === TASK_MAP_FILTER_KEY) {
    taskCompletionFilter.value = DEFAULT_MAP_TASK_COMPLETION_FILTER;
  }
  activeFilter.value = nextFilter;
}

function selectTaskCompletionFilter() {
  if (activeFilter.value !== TASK_MAP_FILTER_KEY || isSearchMode.value) {
    return;
  }

  const options: Array<{ label: string; value: MapTaskCompletionFilter }> = [
    { label: "全部任务", value: "all" },
    { label: "已完成任务", value: "completed" },
    { label: "未完成任务", value: "unfinished" },
  ];
  uni.showActionSheet({
    itemList: options.map((option) => option.label),
    success: ({ tapIndex }) => {
      const option = options[tapIndex];
      if (!option) {
        return;
      }
      taskCompletionFilter.value = option.value;
      selectedSummary.value = null;
      selectedPoiMarker.value = null;
    },
  });
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
  selectedPoiMarker.value = null;
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
  if (isFiniteLngLat(item)) {
    focusMapToPoint(item);
  }

  if (item.map_point_id) {
    upsertShellItemMapMarker(item);
    selectedPoiMarker.value = null;
    void loadPointSummary(item.map_point_id);
    return;
  }

  const summary = buildExternalSummaryFromItem(item);
  selectedSummary.value = summary;
  selectedPoiMarker.value = summary ? buildSelectedPoiMarker(summary) : null;
}

function shellItemPointType(item: MapShellItem): string {
  if (item.type === "daily_task" || item.type === "emergency_task") {
    return "task";
  }
  return item.type;
}

function shellItemBusinessType(item: MapShellItem): string | null {
  if (item.type === "daily_task") {
    return "feeding";
  }
  if (item.type === "emergency_task") {
    return "emergency";
  }
  return null;
}

function shellItemMarkerExtra(item: MapShellItem): Record<string, unknown> {
  const extra: Record<string, unknown> = {};
  if (isTaskShellItem(item)) {
    extra.task_status = item.status_key || null;
    extra.task_status_label = item.status_label || null;
    extra.location_detail = item.description || null;
    if (item.active_execution) {
      extra.active_execution = item.active_execution;
    }
    const activeStatus =
      item.active_execution?.display_status || item.active_execution?.status || item.status_key;
    if (activeStatus === "completed") {
      extra.feeding_status = "completed";
    } else if (activeStatus === "in_progress" || activeStatus === "pending") {
      extra.feeding_status = "pending";
    }
  }
  if (item.associated_poi) {
    extra.associated_poi = item.associated_poi;
  }
  return extra;
}

function shellItemMarkerKey(item: MapShellItem): string | null {
  if (item.icon_key) {
    return item.icon_key;
  }
  if (item.type === "daily_task") {
    return "task_feeding";
  }
  if (item.type === "emergency_task") {
    return "task_emergency";
  }
  return item.type;
}

function buildMapMarkerFromShellItem(item: MapShellItem): MapPointMarkerDto | null {
  if (!item.map_point_id || !isFiniteLngLat(item)) {
    return null;
  }

  return {
    point_id: item.map_point_id,
    point_type: shellItemPointType(item),
    point_scope: "long_term",
    business_type: shellItemBusinessType(item),
    business_id: item.id,
    name: item.title,
    subtitle: item.subtitle,
    lng: item.lng,
    lat: item.lat,
    area_id: null,
    area_name: null,
    marker_key: shellItemMarkerKey(item),
    icon_key: shellItemMarkerKey(item),
    display_level: 85,
    visibility: "public",
    status: "active",
    cover_photo_url: item.cover_photo_url || null,
    preview_enabled: Boolean(item.cover_photo_url),
    preview_min_zoom: 16,
    label_min_zoom: 16,
    distance_meters: item.distance_meters,
    extra: shellItemMarkerExtra(item),
  };
}

function upsertShellItemMapMarker(item: MapShellItem) {
  const marker = buildMapMarkerFromShellItem(item);
  if (marker) {
    upsertFocusedMapMarker(marker);
  }
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

function isTaskShellItem(item: MapShellItem): boolean {
  return item.type === "daily_task" || item.type === "emergency_task";
}

function getShellItemMetaText(item: MapShellItem): string {
  if (isTaskShellItem(item)) {
    return item.description || item.subtitle || "暂无位置补充说明";
  }

  return `· 距离 ${formatDistance(item.distance_meters)}`;
}

function getShellItemStatusTone(item: MapShellItem): string {
  if (!isTaskShellItem(item)) {
    return item.type;
  }

  if (item.status_key === "completed" || item.status_label === "已完成") {
    return "completed";
  }
  if (item.status_key === "in_progress" || item.status_label === "进行中") {
    return "in_progress";
  }
  if (item.status_key === "not_started" || item.status_label === "未开始") {
    return "not_started";
  }
  if (item.status_key === "cancelled" || item.status_label === "已取消") {
    return "cancelled";
  }
  if (item.status_key === "archived" || item.status_label === "已归档") {
    return "archived";
  }
  return item.type;
}

function getFeedingMarkerIcon(marker: MapPointMarkerDto): string {
  const activeExecution = marker.extra.active_execution;
  if (activeExecution && typeof activeExecution === "object") {
    const record = activeExecution as Record<string, unknown>;
    const status = record.display_status || record.status;
    return status === "completed" ? dailyTaskPointIcon : dailyTaskPendingPointIcon;
  }

  return marker.extra.feeding_status === "completed"
    ? dailyTaskPointIcon
    : dailyTaskPendingPointIcon;
}

function getNativeMarkerIcon(
  type: MapShellItemType,
  marker?: MapPointMarkerDto,
): string {
  if (marker && (marker.icon_key === "landmark" || marker.business_type === "tencent_poi")) {
    return landmarkPointIcon;
  }

  if (marker && marker.business_type === "feeding") {
    return getFeedingMarkerIcon(marker);
  }

  const icons: Record<MapShellItemType, string> = {
    emergency_task: emergencyTaskPointIcon,
    daily_task: dailyTaskPointIcon,
    cat: catPointMarkerIcon,
    supply: supplyPointMarkerIcon,
    landmark: landmarkPointIcon,
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

function getNativeMapContext(): NativeMapContext {
  return uni.createMapContext("campus-map") as unknown as NativeMapContext;
}

function invalidateMapCenterMovement() {
  mapCenterMoveRequestId += 1;
}

function moveNativeMapToPoint(nextCenter: LngLat) {
  const requestId = ++mapCenterMoveRequestId;
  const mapContext = getNativeMapContext();
  const syncLatestCenter = () => {
    if (requestId !== mapCenterMoveRequestId) {
      return;
    }
    syncMapCenterFromNative(nextCenter);
  };

  if (typeof mapContext.moveToLocation !== "function") {
    syncLatestCenter();
    return;
  }

  mapContext.moveToLocation({
    longitude: nextCenter.lng,
    latitude: nextCenter.lat,
    success: syncLatestCenter,
    fail: syncLatestCenter,
  });
}

function centerMapToPoint(point: LngLat, options: { smooth?: boolean } = {}) {
  const nextCenter = clampLngLatToBounds(point, campusMapConfig.value.limit_bounds);
  if (options.smooth) {
    moveNativeMapToPoint(nextCenter);
    return;
  }
  invalidateMapCenterMovement();
  syncMapCenterFromNative(nextCenter);
}

function centerMapToCampus() {
  centerMapToPoint(campusMapConfig.value.center);
}

function syncUserLocation(point: LngLat | null) {
  userLocation.value = point ? { lng: point.lng, lat: point.lat } : null;
}

function focusMapToPoint(point: LngLat) {
  const targetScale = getClampedMapScale(
    getMapFocusTargetScale(observedMapScale.value, MAP_POINT_FOCUS_SCALE),
  );
  if (
    !Number.isFinite(observedMapScale.value) ||
    targetScale > observedMapScale.value + MAP_SCALE_SYNC_EPSILON
  ) {
    setControlledMapScale(targetScale);
  }
  centerMapToPoint(point, { smooth: true });
}

function isSameMapCenter(a: LngLat, b: LngLat): boolean {
  return distanceMetersBetween(a, b) <= MAP_CENTER_SYNC_EPSILON_METERS;
}

function syncMapCenterFromNative(nextCenter: LngLat) {
  if (!isSameMapCenter(mapCenter.value, nextCenter)) {
    mapCenter.value = nextCenter;
  }
}

function recordNativeMapScale(nextScale: number) {
  const clampedScale = getClampedMapScale(nextScale);
  if (Math.abs(observedMapScale.value - clampedScale) >= MAP_SCALE_SYNC_EPSILON) {
    observedMapScale.value = clampedScale;
  }
}

function setControlledMapScale(nextScale: number) {
  const clampedScale = getClampedMapScale(nextScale);
  if (Math.abs(mapScale.value - clampedScale) >= MAP_SCALE_SYNC_EPSILON) {
    mapScale.value = clampedScale;
  }
  recordNativeMapScale(clampedScale);
}

function syncMapScaleFromContext(onComplete?: () => void) {
  const mapContext = uni.createMapContext("campus-map") as unknown as NativeMapContext;
  if (typeof mapContext.getScale !== "function") {
    onComplete?.();
    return;
  }
  let completed = false;
  const completeOnce = () => {
    if (completed) {
      return;
    }
    completed = true;
    onComplete?.();
  };
  mapContext.getScale({
    success: (result) => {
      recordNativeMapScale(Number(result.scale));
      completeOnce();
    },
    fail: completeOnce,
    complete: completeOnce,
  });
  setTimeout(completeOnce, 120);
}

function getClampedMapScale(targetScale: number): number {
  const minScale = campusMapConfig.value.min_zoom;
  const maxScale = campusMapConfig.value.max_zoom;
  return Math.min(Math.max(targetScale, minScale), maxScale);
}

async function getCurrentLocationForNavigation(): Promise<LngLat | null> {
  const cached = userLocation.value || getCachedUserLocation();
  if (cached) {
    return { lng: cached.lng, lat: cached.lat };
  }

  const point = await preloadUserLocation({ silent: true });
  return point ? { lng: point.lng, lat: point.lat } : null;
}

function clearNativeRoute() {
  nativeRoutePoints.value = [];
  navigationRoute.value = null;
}

function fitNativeMapToRoute(points: NativeRoutePoint[]): boolean {
  if (points.length < 2) {
    return false;
  }

  const mapContext = uni.createMapContext("campus-map") as unknown as NativeMapContext;
  if (typeof mapContext.includePoints !== "function") {
    return false;
  }

  mapContext.includePoints({
    points,
    padding: [72, 72, 280, 72],
  });
  return true;
}

function renderNativeRoute(from: LngLat, destination: LngLat, routePoints?: LngLat[]) {
  clearNativeRoute();
  const routeLngLatPoints = (routePoints && routePoints.length >= 2 ? routePoints : [from, destination])
    .filter(isFiniteLngLat);
  nativeRoutePoints.value = routeLngLatPoints
    .map((point) => toNativeMapPoint(point))
    .filter(
      (point): point is NativeRoutePoint =>
        Boolean(point),
    );
  const routeFitted = fitNativeMapToRoute(nativeRoutePoints.value);
  if (!routeFitted) {
    centerMapToPoint({
      lng: (from.lng + destination.lng) / 2,
      lat: (from.lat + destination.lat) / 2,
    }, { smooth: true });
  }
}

function isSameRoutePoint(a: LngLat, b: LngLat): boolean {
  return Math.abs(a.lng - b.lng) < 0.000001 && Math.abs(a.lat - b.lat) < 0.000001;
}

function buildDisplayRoutePoints(
  from: LngLat,
  destination: LngLat,
  routePoints: LngLat[],
): LngLat[] {
  const displayRoutePoints: LngLat[] = [];
  for (const point of [from, ...routePoints, destination]) {
    if (!isFiniteLngLat(point)) {
      continue;
    }
    const lastPoint = displayRoutePoints[displayRoutePoints.length - 1];
    if (!lastPoint || !isSameRoutePoint(lastPoint, point)) {
      displayRoutePoints.push(point);
    }
  }
  return displayRoutePoints;
}

function mapSearchShellItemToMarker(item: MapShellItem): MapPointMarkerDto | null {
  if (!isFiniteLngLat(item)) {
    return null;
  }
  if (!isLngLatInsideBounds(item, campusMapConfig.value.limit_bounds)) {
    return null;
  }

  const isTask = item.type === "emergency_task" || item.type === "daily_task";
  const isExternalPoi = Boolean(
    item.associated_poi || (!item.map_point_id && item.type === "landmark"),
  );
  const pointType = isTask ? "task" : item.type;
  const businessType =
    isExternalPoi
      ? "tencent_poi"
      : item.type === "emergency_task"
        ? "emergency"
        : item.type === "daily_task"
          ? "daily"
          : null;
  const markerIconKey =
    businessType === "tencent_poi" ? "landmark" : item.icon_key || item.type;

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
    marker_key: markerIconKey,
    icon_key: isExternalPoi ? "landmark" : markerIconKey,
    display_level: 80,
    visibility: "public",
    status: "active",
    cover_photo_url: item.cover_photo_url || null,
    preview_enabled: !isExternalPoi,
    preview_min_zoom: 18,
    label_min_zoom: 16,
    distance_meters: item.distance_meters,
    extra: {
      source: "map_search",
      is_external_poi: isExternalPoi,
      associated_poi: item.associated_poi || null,
    },
  };
}

function buildExternalSummaryFromItem(item: MapShellItem): MapPointSummaryResponse | null {
  if (
    !isFiniteLngLat(item) ||
    !isLngLatInsideBounds(item, campusMapConfig.value.limit_bounds)
  ) {
    return null;
  }
  return {
    point_id: item.id,
    point_type: "landmark",
    business_type: "tencent_poi",
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
    associated_poi: item.associated_poi || null,
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
    business_type: "tencent_poi",
    business_id: marker.business_id,
    title: marker.name,
    subtitle: marker.subtitle,
    cover_photo_url: marker.cover_photo_url || null,
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
    associated_poi: (marker.extra.associated_poi || null) as MapPointSummaryResponse["associated_poi"],
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

function buildSelectedPoiMarker(
  summary: MapPointSummaryResponse,
): MapPointMarkerDto | null {
  if (
    summary.business_type !== "tencent_poi" ||
    !isFiniteLngLat({ lng: summary.lng, lat: summary.lat }) ||
    !isLngLatInsideBounds(
      { lng: summary.lng, lat: summary.lat },
      campusMapConfig.value.limit_bounds,
    )
  ) {
    return null;
  }

  return {
    point_id: summary.point_id,
    point_type: "landmark",
    point_scope: "search_result",
    business_type: "tencent_poi",
    business_id: summary.business_id || summary.point_id,
    name: summary.title,
    subtitle: summary.subtitle || summary.location_detail,
    lng: summary.lng,
    lat: summary.lat,
    area_id: null,
    area_name: null,
    marker_key: "landmark",
    icon_key: "landmark",
    display_level: 90,
    visibility: "public",
    status: "active",
    cover_photo_url: summary.cover_photo_url || null,
    preview_enabled: false,
    preview_min_zoom: 18,
    label_min_zoom: 16,
    distance_meters: summary.distance_meters,
    extra: {
      source: "selected_poi",
      is_external_poi: true,
      associated_poi: summary.associated_poi || null,
    },
  };
}

function applyMapInit(data: MapInitResponse) {
  const coreBounds = isFiniteLngLatBounds(data.campus.core_bounds)
    ? data.campus.core_bounds
    : HBNU_CAMPUS_CORE_BOUNDS;
  const limitBounds = isFiniteLngLatBounds(data.campus.limit_bounds)
    ? data.campus.limit_bounds
    : expandLngLatBounds(coreBounds, 0.35);
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
    limit_bounds: limitBounds,
  };
  setControlledMapScale(campusMapConfig.value.default_zoom);
  centerMapToPoint(campusMapConfig.value.center);
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

  const filterKey = activeFilter.value;
  const filterOption = activeFilterOption.value;

  if (!filterKey) {
    mapPointFilterReady.value = true;
    clearViewportMarkerBubbles();
    mapPointMarkers.value = [];
    if (selectedSummary.value && selectedSummary.value.business_type !== "tencent_poi") {
      ensureFocusedMarkerFromSummary(selectedSummary.value);
    }
    if (!isSearchMode.value) {
      await loadBottomContent();
    }
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    mapPointFilterReady.value = false;
    return;
  }

  mapPointFilterReady.value = false;
  clearViewportMarkerBubbles();

  if (!isSearchMode.value) {
    contentLoadState.value = "loading";
  }

  try {
    const data = await getMapPoints(token, {
      campus_id: campusMapConfig.value.id,
      ...getMapPointQueryByFilter(filterKey, filterOption),
      ...getViewportQuery(),
    });
    if (activeFilter.value !== filterKey) {
      return;
    }
    mapPointMarkers.value = data.items.filter(
      (marker) =>
        isFiniteLngLat({ lng: marker.lng, lat: marker.lat }) &&
        isLngLatInsideBounds(marker, campusMapConfig.value.limit_bounds),
    );
    if (activeFilter.value && !isSearchMode.value) {
      bottomContentItems.value = mapPointMarkers.value.map(mapMarkerToShellItem);
      contentLoadState.value = "ready";
    }
    mapPointFilterReady.value = true;
    refreshViewportMarkerBubbles();
  } catch (error) {
    if (activeFilter.value === filterKey) {
      mapPointFilterReady.value = false;
      clearViewportMarkerBubbles();
    }
    contentLoadState.value = "error";
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
    selectedPoiMarker.value = null;
    contentLoadState.value = "ready";
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    return;
  }

  contentLoadState.value = "loading";
  selectedSummary.value = null;
  selectedPoiMarker.value = null;
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
        isFiniteLngLat(item) &&
        isLngLatInsideBounds(item, campusMapConfig.value.limit_bounds) &&
        (!activeFilter.value ||
          activeFilter.value === ALL_MAP_FILTER_KEY ||
          isMapShellItemVisibleByFilter(item, activeFilter.value))
      );
    });
    searchResultItems.value = items;
    mapPointMarkers.value = items
      .map(mapSearchShellItemToMarker)
      .filter((marker): marker is MapPointMarkerDto => Boolean(marker));
    contentLoadState.value = "ready";
    mapPointFilterReady.value = Boolean(activeFilter.value);
    refreshViewportMarkerBubbles();
  } catch (error) {
    searchResultItems.value = [];
    mapPointMarkers.value = [];
    mapPointFilterReady.value = false;
    clearViewportMarkerBubbles();
    contentLoadState.value = "error";
    handleMapError(error, "搜索失败，请稍后重试。");
  }
}

async function loadPointSummary(pointId: string) {
  const requestId = startPointSummaryRequest();
  contentLoadState.value = "loading";
  selectedPoiMarker.value = null;
  try {
    const token = await getAccessToken();
    if (!isCurrentPointSummaryRequest(requestId)) {
      return;
    }
    if (!token) {
      contentLoadState.value = "ready";
      return;
    }

    const summary = await getMapPointSummary(token, pointId);
    if (!isCurrentPointSummaryRequest(requestId)) {
      return;
    }

    selectedSummary.value = summary;
    ensureFocusedMarkerFromSummary(summary);
    const summaryPoint = {
      lng: summary.lng,
      lat: summary.lat,
    };
    if (isFiniteLngLat(summaryPoint)) {
      focusMapToPoint(summaryPoint);
    }
    contentLoadState.value = "ready";
  } catch (error) {
    if (!isCurrentPointSummaryRequest(requestId)) {
      return;
    }
    selectedSummary.value = null;
    contentLoadState.value = "error";
    handleMapError(error, "点位详情加载失败");
  } finally {
    finishPointSummaryRequest(requestId);
  }
}

function getExecutionDateIdFromValue(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  return typeof record.execution_date_id === "string" ? record.execution_date_id : null;
}

function selectedSummaryExecutionDateId(): string | null {
  return (
    getExecutionDateIdFromValue(selectedSummary.value?.business_summary?.active_execution) ||
    getExecutionDateIdFromValue(selectedPoiMarker.value?.extra?.active_execution)
  );
}

function appendExecutionDateQuery(path: string, executionDateId: string | null): string {
  if (!executionDateId || path.includes("execution_date_id=")) {
    return path;
  }
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}execution_date_id=${executionDateId}`;
}

async function handleSummaryAction(action: CardActionDto) {
  if (!action.enabled || !selectedSummary.value) {
    return;
  }

  if (action.key === "view_detail") {
    if (action.target_type === "page" && action.path) {
      uni.navigateTo({
        url: appendExecutionDateQuery(action.path, selectedSummaryExecutionDateId()),
      });
      return;
    }

    if (selectedSummary.value.business_type === "feeding" && selectedSummary.value.business_id) {
      uni.navigateTo({
        url: appendExecutionDateQuery(
          `/pages/tasks/detail?task_id=${selectedSummary.value.business_id}`,
          selectedSummaryExecutionDateId(),
        ),
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
    const from = await getCurrentLocationForNavigation();
    if (!from) {
      uni.showToast({ title: "无法获取当前位置", icon: "none" });
      return;
    }
    if (selectedSummary.value.business_type === "tencent_poi") {
      const route = await getWalkingRoute(token, {
        from_lng: from.lng,
        from_lat: from.lat,
        to_lng: selectedSummary.value.lng,
        to_lat: selectedSummary.value.lat,
      });
      renderInAppRoute(from, {
        point_id: selectedSummary.value.point_id,
        title: selectedSummary.value.title,
        destination: {
          lng: selectedSummary.value.lng,
          lat: selectedSummary.value.lat,
          location_name: selectedSummary.value.location_name || selectedSummary.value.title,
          amap_poi_id: null,
          amap_address: null,
          associated_poi: selectedSummary.value.associated_poi || null,
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
        tencent_navigation: {
          mode: "walking",
          web_url: "",
        },
        route,
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

function buildExternalSummaryFromPoi(
  poi: NonNullable<MapPointSummaryResponse["associated_poi"]>,
): MapPointSummaryResponse | null {
  return buildExternalSummaryFromItem({
    id: `tencent:${poi.poi_id || `${poi.name}-${poi.lng}-${poi.lat}`}`,
    type: "landmark",
    title: poi.name,
    subtitle: poi.category,
    description: poi.address,
    distance_meters: poi.distance_meters,
    status_label: "地图点位",
    tag_label: "地标",
    lng: poi.lng,
    lat: poi.lat,
    icon_key: "landmark",
    associated_poi: poi,
  });
}

function createFocusedMarkerFromSummary(summary: MapPointSummaryResponse): MapPointMarkerDto {
  return {
    point_id: summary.point_id,
    point_type: summary.point_type,
    point_scope: "temporary",
    business_type: summary.business_type,
    business_id: summary.business_id || summary.point_id,
    name: summary.title,
    subtitle: summary.subtitle || summary.location_name,
    lng: summary.lng,
    lat: summary.lat,
    area_id: null,
    area_name: null,
    marker_key: summary.business_type || summary.point_type,
    icon_key: summary.business_type || summary.point_type,
    display_level: 100,
    visibility: "public",
    status: "active",
    cover_photo_url: summary.cover_photo_url || null,
    preview_enabled: true,
    preview_min_zoom: 15,
    label_min_zoom: 16,
    distance_meters: summary.distance_meters,
    extra: {
      source: "task_detail_focus",
      associated_poi: summary.associated_poi || null,
    },
  };
}

function upsertFocusedMapMarker(marker: MapPointMarkerDto) {
  if (mapPointMarkers.value.some((item) => item.point_id === marker.point_id)) {
    return;
  }

  mapPointMarkers.value = [...mapPointMarkers.value, marker];
}

function ensureFocusedMarkerFromSummary(summary: MapPointSummaryResponse) {
  const marker = createFocusedMarkerFromSummary(summary);
  upsertFocusedMapMarker(marker);
}

function syncFocusedMarkerFromSummary(summary: MapPointSummaryResponse) {
  ensureFocusedMarkerFromSummary(summary);
  bottomContentItems.value = mapPointMarkers.value.map(mapMarkerToShellItem);
}

function focusPendingPoi(poi: NonNullable<MapPointSummaryResponse["associated_poi"]>) {
  const summary = buildExternalSummaryFromPoi(poi);
  if (!summary) {
    return;
  }
  clearNativeRoute();
  selectedSummary.value = summary;
  selectedPoiMarker.value = buildSelectedPoiMarker(summary);
  contentLoadState.value = "ready";
  focusMapToPoint({ lng: summary.lng, lat: summary.lat });
}

async function loadPendingNavigationSummary(pending: PendingMapNavigation) {
  clearNativeRoute();
  if (pending.poi) {
    focusPendingPoi(pending.poi);
    return;
  }
  if (!pending.map_point_id) {
    return;
  }

  if (pending.shell_item) {
    upsertShellItemMapMarker(pending.shell_item);
  }
  await loadPointSummary(pending.map_point_id);
  if (!selectedSummary.value) {
    return;
  }
  syncFocusedMarkerFromSummary(selectedSummary.value);
  selectedPoiMarker.value = null;
}

function consumePendingNavigation() {
  const pending = uni.getStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY) as
    | PendingMapNavigation
    | "";
  if (!pending || typeof pending !== "object") {
    return;
  }
  uni.removeStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY);
  void loadPendingNavigationSummary(pending);
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
  markPointTapInteraction();
  const markerId = (event as CustomEvent<{ markerId?: number }>).detail?.markerId;
  if (!markerId) {
    return;
  }

  const marker = findNativeMarkerByStableId(markerId);
  if (!marker) {
    return;
  }

  focusMapToPoint({ lng: marker.lng, lat: marker.lat });
  handleMapMarkerSelected(marker);
}

function handleNativeMapTap() {
  if (mapPointEditMode.value || shouldIgnoreNativeMapTap()) {
    return;
  }
  clearSelectedMapPointState();
}

async function handleNativePoiTap(event: Event) {
  if (isNativePoiTapSuppressed()) {
    return;
  }
  markPointTapInteraction();
  const detail = (event as CustomEvent<Record<string, any>>).detail || {};
  const rawPoi = detail.poi || {};
  const lng = Number(detail.longitude ?? detail.lng ?? rawPoi.longitude ?? rawPoi.lng);
  const lat = Number(detail.latitude ?? detail.lat ?? rawPoi.latitude ?? rawPoi.lat);
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
    return;
  }
  if (!isLngLatInsideBounds({ lng, lat }, campusMapConfig.value.limit_bounds)) {
    return;
  }
  const keyword = String(detail.name || detail.title || rawPoi.name || rawPoi.title || "");
  const poiTapKey = getPoiTapKey({ lng, lat, keyword });
  if (shouldSkipPoiResolve(poiTapKey, { lng, lat, keyword })) {
    return;
  }
  const resolveRequestId = startPoiResolve(poiTapKey);
  const token = await getAccessToken();
  if (!token) {
    finishPoiResolve(resolveRequestId, poiTapKey);
    return;
  }
  try {
    const data = await resolveMapPoi(token, {
      keyword,
      lng,
      lat,
    });
    const poi = data.matched_poi;
    if (
      !isLngLatInsideBounds(
        { lng: poi.lng, lat: poi.lat },
        campusMapConfig.value.limit_bounds,
      )
    ) {
      return;
    }
    if (!isCurrentPoiResolve(resolveRequestId)) {
      return;
    }
    const item: MapShellItem = {
      id: `tencent:${poi.poi_id || `${poi.name}-${poi.lng}-${poi.lat}`}`,
      type: "landmark",
      title: poi.name,
      subtitle: poi.category,
      description: poi.address,
      distance_meters: poi.distance_meters,
      status_label: "地图点位",
      tag_label: "地标",
      lng: poi.lng,
      lat: poi.lat,
      icon_key: "landmark",
      associated_poi: poi,
    };
    const summary = buildExternalSummaryFromItem(item);
    if (summary) {
      selectedSummary.value = summary;
      selectedPoiMarker.value = buildSelectedPoiMarker(summary);
      lastResolvedPoiTapKey.value = poiTapKey;
      suppressNativePoiTaps();
      focusMapToPoint({ lng: summary.lng, lat: summary.lat });
      contentLoadState.value = "ready";
    }
  } catch (error) {
    handleMapError(error, "地图点位解析失败");
    uni.showToast({ title: contentErrorMessage.value, icon: "none" });
  } finally {
    finishPoiResolve(resolveRequestId, poiTapKey);
  }
}

function handleNativeMarkerLongPress(event: Event) {
  const markerId = (event as CustomEvent<{ markerId?: number }>).detail?.markerId;
  if (!markerId) {
    return;
  }

  const marker = findNativeMarkerByStableId(markerId);
  if (marker) {
    void enterMapPointEditMode(marker);
  }
}

function distanceMetersBetween(from: LngLat, to: LngLat): number {
  const earthRadiusMeters = 6371000;
  const lat1 = (from.lat * Math.PI) / 180;
  const lat2 = (to.lat * Math.PI) / 180;
  const deltaLat = ((to.lat - from.lat) * Math.PI) / 180;
  const deltaLng = ((to.lng - from.lng) * Math.PI) / 180;
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;

  return earthRadiusMeters * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function findNearestEditableMarker(point: LngLat): MapPointMarkerDto | null {
  const nearest = mapPointMarkers.value
    .filter(
      (marker) =>
        marker.business_type !== "tencent_poi" &&
        isFiniteLngLat({ lng: marker.lng, lat: marker.lat }),
    )
    .map((marker) => ({
      marker,
      distance: distanceMetersBetween(point, { lng: marker.lng, lat: marker.lat }),
    }))
    .sort((a, b) => a.distance - b.distance)[0];

  return nearest && nearest.distance <= MARKER_LONG_PRESS_HIT_METERS
    ? nearest.marker
    : null;
}

async function enterMapPointEditMode(marker: MapPointMarkerDto, location?: LngLat) {
  if (!userStore.isAdmin) {
    return;
  }
  if (marker.point_scope === "search_result" && marker.extra.is_external_poi) {
    uni.showToast({ title: "外部地图点位不能编辑", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  try {
    selectedSummary.value =
      selectedSummary.value?.point_id === marker.point_id
        ? selectedSummary.value
        : await getMapPointSummary(token, marker.point_id);
    editedPointLocation.value = clampLngLatToBounds(
      location || { lng: marker.lng, lat: marker.lat },
      campusMapConfig.value.limit_bounds,
    );
    editableMarkerScreenPosition.value = null;
    mapPointEditMode.value = true;
    centerMapToPoint(editedPointLocation.value, { smooth: true });
    uni.showToast({ title: "已进入点位编辑模式", icon: "none" });
  } catch (error) {
    handleMapError(error, "点位详情加载失败");
    uni.showToast({ title: contentErrorMessage.value, icon: "none" });
  }
}

function handleMarkerLongPress(event: Event) {
  if (!userStore.isAdmin) {
    return;
  }
  const detail = (event as CustomEvent<{ longitude?: number; latitude?: number }>).detail;
  if (typeof detail?.longitude !== "number" || typeof detail?.latitude !== "number") {
    return;
  }
  const pressPoint = clampLngLatToBounds(
    { lng: detail.longitude, lat: detail.latitude },
    campusMapConfig.value.limit_bounds,
  );
  const marker = findNearestEditableMarker(pressPoint);
  if (!marker) {
    return;
  }
  void enterMapPointEditMode(marker, pressPoint);
}

function getMapRegionChangeDetail(event: Event): NativeRegionChangeDetail {
  const rawEvent = event as Event & Record<string, any>;
  const detail = (rawEvent.detail || {}) as Record<string, any>;
  const nestedDetail = (detail.detail || {}) as Record<string, any>;
  const rawType = [detail.type, nestedDetail.type, rawEvent.type].find(
    (value) => value === "begin" || value === "end",
  );
  const rawCausedBy = detail.causedBy ?? nestedDetail.causedBy ?? rawEvent.causedBy;
  const rawScale = detail.scale ?? nestedDetail.scale ?? rawEvent.scale;
  const scale = Number(rawScale);
  const centerLocation =
    detail.centerLocation ?? nestedDetail.centerLocation ?? rawEvent.centerLocation;

  return {
    type: typeof rawType === "string" ? rawType : undefined,
    causedBy: typeof rawCausedBy === "string" ? rawCausedBy : undefined,
    scale: Number.isFinite(scale) ? scale : undefined,
    centerLocation:
      typeof centerLocation?.longitude === "number" &&
      typeof centerLocation?.latitude === "number"
        ? centerLocation
        : undefined,
  };
}

function handleMapRegionChange(event: Event) {
  const detail = getMapRegionChangeDetail(event);
  if (drawerResizeInProgress.value) {
    clearViewportMarkerBubbles(false);
    return;
  }
  const shouldQueryScale = shouldQueryMapScaleFromRegionChange(detail);
  if (shouldSyncMapScaleFromRegionChange(detail)) {
    recordNativeMapScale(Number(detail.scale));
  }
  if (detail?.type && detail.type !== "end") {
    clearViewportMarkerBubbles(false);
    if (detail.causedBy === "drag") {
      invalidateMapCenterMovement();
    }
    return;
  }
  const center = detail?.centerLocation;
  if (typeof center?.longitude !== "number" || typeof center?.latitude !== "number") {
    if (shouldQueryScale) {
      syncMapScaleFromContext(refreshViewportMarkerBubbles);
    } else {
      refreshViewportMarkerBubbles();
    }
    return;
  }

  const nextCenter = clampLngLatToBounds(
    { lng: center.longitude, lat: center.latitude },
    campusMapConfig.value.limit_bounds,
  );
  if (nextCenter.lng !== center.longitude || nextCenter.lat !== center.latitude) {
    if (!isSameMapCenter(mapCenter.value, nextCenter)) {
      centerMapToPoint(nextCenter, { smooth: true });
    }
  } else if (detail.causedBy === "update") {
    // Programmatic center changes already flow through mapCenter; echoing them here can retrigger native map movement.
  } else {
    syncMapCenterFromNative(nextCenter);
  }

  if (!mapPointEditMode.value || editableMarkerScreenPosition.value) {
    if (shouldQueryScale) {
      syncMapScaleFromContext(refreshViewportMarkerBubbles);
    } else {
      refreshViewportMarkerBubbles();
    }
    return;
  }
  editedPointLocation.value = nextCenter;
  if (shouldQueryScale) {
    syncMapScaleFromContext(refreshViewportMarkerBubbles);
  } else {
    refreshViewportMarkerBubbles();
  }
}

function getMapViewportOffset() {
  const ratio = drawerConfig.value.rpxRatio;
  return {
    left: 24 * ratio,
    top: 218 * ratio,
  };
}

function getTouchClientPosition(event: Event): { clientX: number; clientY: number } | null {
  const touchEvent = event as unknown as {
    touches?: Array<{ clientX?: number; clientY?: number; x?: number; y?: number }>;
    changedTouches?: Array<{ clientX?: number; clientY?: number; x?: number; y?: number }>;
  };
  const touch = touchEvent.touches?.[0] || touchEvent.changedTouches?.[0];
  const clientX = touch?.clientX ?? touch?.x;
  const clientY = touch?.clientY ?? touch?.y;

  return typeof clientX === "number" && typeof clientY === "number"
    ? { clientX, clientY }
    : null;
}

function updateEditedPointFromScreenPosition(position: { x: number; y: number }) {
  const mapContext = uni.createMapContext("campus-map") as unknown as {
    fromScreenLocation?: (options: {
      x: number;
      y: number;
      success?: (result: { longitude?: number; latitude?: number }) => void;
      fail?: () => void;
    }) => void;
  };

  if (typeof mapContext.fromScreenLocation !== "function") {
    editedPointLocation.value = clampLngLatToBounds(
      mapCenter.value,
      campusMapConfig.value.limit_bounds,
    );
    return;
  }

  mapContext.fromScreenLocation({
    x: position.x,
    y: position.y,
    success: (result) => {
      if (typeof result.longitude === "number" && typeof result.latitude === "number") {
        editedPointLocation.value = clampLngLatToBounds(
          {
            lng: result.longitude,
            lat: result.latitude,
          },
          campusMapConfig.value.limit_bounds,
        );
      }
    },
    fail: () => {
      editedPointLocation.value = clampLngLatToBounds(
        mapCenter.value,
        campusMapConfig.value.limit_bounds,
      );
    },
  });
}

function dragEditedPoint(event: Event) {
  if (!mapPointEditMode.value) {
    return;
  }
  const touch = getTouchClientPosition(event);
  if (!touch) {
    return;
  }
  const offset = getMapViewportOffset();
  const position = {
    x: Math.max(0, touch.clientX - offset.left),
    y: Math.max(0, touch.clientY - offset.top),
  };
  editableMarkerScreenPosition.value = position;
  updateEditedPointFromScreenPosition(position);
}

function finishDraggingEditedPoint(event: Event) {
  dragEditedPoint(event);
}

function handleMapMarkerSelected(marker: MapPointMarkerDto) {
  if (marker.point_scope === "search_result" && marker.extra.is_external_poi) {
    selectedPoiMarker.value = marker;
    selectedSummary.value = buildExternalSummaryFromMarker(marker);
    return;
  }
  selectedPoiMarker.value = null;
  void loadPointSummary(marker.point_id);
}

function cancelMapPointEditMode() {
  mapPointEditMode.value = false;
  editedPointLocation.value = null;
  editableMarkerScreenPosition.value = null;
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
    const nextLocation = clampLngLatToBounds(
      editedPointLocation.value,
      campusMapConfig.value.limit_bounds,
    );
    const updated = await updateAdminMapPointLocation(
      token,
      selectedSummary.value.point_id,
      nextLocation,
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
    centerMapToPoint({ lng: updated.lng, lat: updated.lat }, { smooth: true });
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
  if (navigation.route.fallback) {
    clearNativeRoute();
    navigationRoute.value = {
      title: navigation.title,
      distance_meters: navigation.route.distance_meters,
      duration_seconds: navigation.route.duration_seconds,
      points: [],
      steps: navigation.route.steps,
    };
    centerMapToPoint(destination, { smooth: true });
    uni.showToast({ title: "路线规划暂不可用，已定位到目的地", icon: "none" });
    return;
  }
  const routePoints = navigation.route.points.length
    ? navigation.route.points
    : [from, destination];
  const safeRoutePoints = routePoints.filter(isFiniteLngLat);
  const displayRoutePoints = buildDisplayRoutePoints(from, destination, safeRoutePoints);
  renderNativeRoute(from, destination, displayRoutePoints);
  navigationRoute.value = {
    title: navigation.title,
    distance_meters: navigation.route.distance_meters,
    duration_seconds: navigation.route.duration_seconds,
    points: displayRoutePoints,
    steps: navigation.route.steps,
  };
}

function locateMe() {
  const point = userLocation.value || getCachedUserLocation();
  if (!point) {
    uni.showToast({ title: "无法获取当前位置", icon: "none" });
    return;
  }
  clearNativePoiSelection();
  suppressNativePoiTaps();
  focusMapToPoint(point);
}

watch(activeFilter, () => {
  selectedSummary.value = null;
  selectedPoiMarker.value = null;
  mapPointFilterReady.value = false;
  clearViewportMarkerBubbles();
  void refreshMapPoints();
  if (isSearchMode.value) {
    void runSearch(searchKeyword.value);
  }
});

watch(taskCompletionFilter, () => {
  refreshViewportMarkerBubbles();
});

watch(searchKeyword, (keyword) => {
  selectedSummary.value = null;
  selectedPoiMarker.value = null;
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
  unsubscribeUserLocation = subscribeUserLocation(syncUserLocation);
  void preloadUserLocation({ silent: true });
  void loadInitialMapData();
});

onShow(() => {
  isPageVisible.value = true;
  void refreshMapFilterOptions()
    .then(() => refreshMapPoints())
    .then(() => consumePendingNavigation());
});

onHide(() => {
  isPageVisible.value = false;
  clearViewportMarkerBubbles(false);
  if (mapRefreshTimer) {
    clearTimeout(mapRefreshTimer);
  }
});

onBeforeUnmount(() => {
  unsubscribeUserLocation?.();
  unsubscribeUserLocation = null;
  invalidateMapCenterMovement();

  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  if (mapRefreshTimer) {
    clearTimeout(mapRefreshTimer);
  }

  if (drawerResizeResumeTimer) {
    clearTimeout(drawerResizeResumeTimer);
  }

  clearViewportMarkerBubbles(false);
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
  position: absolute;
  left: 0;
  top: 0;
  width: 750rpx;
  height: calc(100vh - 288rpx);
  transform: translate(-24rpx, -194rpx);
  transform-origin: left top;
}

.marker-bubble {
  position: absolute;
  z-index: 4;
  max-width: 220rpx;
  box-sizing: border-box;
  padding: 10rpx 14rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8rpx 20rpx rgba(17, 24, 39, 0.16);
  color: #374151;
  font-size: 20rpx;
  font-weight: 800;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
  transform: translate(-50%, -132%);
  transform-origin: center bottom;
  animation: marker-bubble-appear 180ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes marker-bubble-appear {
  from {
    opacity: 0;
    transform: translate(-50%, -132%) scale(0.72);
  }

  to {
    opacity: 1;
    transform: translate(-50%, -132%) scale(1);
  }
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
  top: 380rpx;
  width: 360rpx;
  pointer-events: none;
}

/* 预览大图时仅隐藏不卸载：drawer.wxs 写在该节点上的内联定位样式
   得以保留，退出预览不会出现位置回跳闪烁 */
.map-filter-layer--preview-open {
  display: none;
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
.navigation-end-button::after,
.map-edit-button::after,
.summary-photo-cell::after {
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
  width: 224rpx;
  box-sizing: border-box;
  margin-top: 14rpx;
  padding: 12rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 38rpx rgba(20, 28, 40, 0.13);
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  opacity: 1;
  transform: translateY(0);
  transform-origin: top left;
  pointer-events: auto;
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

.editable-marker-handle {
  position: absolute;
  z-index: 6;
  width: 64rpx;
  height: 64rpx;
  margin-left: -32rpx;
  margin-top: -64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 34rpx rgba(20, 28, 40, 0.16);
}

.editable-marker-icon {
  width: 64rpx;
  height: 64rpx;
}

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

.map-edit-title {
  color: #111827;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.15;
}

.map-edit-desc {
  color: #6b7280;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1.35;
}

.navigation-end-button,
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

.navigation-end-button {
  width: 96rpx;
}

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

.section-title-trigger {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.section-title-arrow {
  color: #6b7280;
  font-size: 22rpx;
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

.navigation-route-card {
  box-sizing: border-box;
  padding: 22rpx;
  border: 2rpx solid rgba(38, 123, 47, 0.16);
  border-radius: 26rpx;
  background: rgba(244, 251, 239, 0.96);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.navigation-route-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 96rpx;
  align-items: center;
  gap: 16rpx;
}

.navigation-route-title {
  display: block;
  color: #111827;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 1.18;
}

.navigation-route-meta,
.navigation-route-step {
  display: block;
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.45;
}

.navigation-route-meta {
  margin-top: 8rpx;
}

.navigation-route-steps {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.navigation-route-step {
  padding: 14rpx 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.76);
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

.summary-avatar-image {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  overflow: hidden;
  background: #edf8e8;
  box-shadow: 0 9rpx 18rpx rgba(17, 24, 39, 0.12);
}

.summary-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.summary-title-row {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.summary-title {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 1.15;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-type-badge {
  flex-shrink: 0;
  max-width: 156rpx;
  box-sizing: border-box;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #edf8e8;
  color: #267b2f;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-subtitle,
.summary-location {
  color: #7e8591;
  font-size: 23rpx;
  font-weight: 800;
}

.summary-photo-strip {
  width: 100%;
}

.summary-photo-grid {
  display: grid;
  gap: 10rpx;
}

.summary-photo-grid.count-1 {
  grid-template-columns: minmax(0, 1fr);
}

.summary-photo-grid.count-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-photo-grid.count-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.summary-photo-cell {
  height: 156rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #edf8e8;
  overflow: hidden;
  line-height: 1;
}

.summary-photo-thumb {
  width: 100%;
  height: 100%;
  display: block;
}

.summary-photo-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.summary-desc {
  color: #4b5563;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.55;
}

.summary-poi {
  padding: 14rpx 16rpx;
  border-radius: 18rpx;
  background: #f6fbf2;
}

.summary-poi-title,
.summary-poi-desc {
  display: block;
}

.summary-poi-title {
  color: #267b2f;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1.35;
}

.summary-poi-desc {
  margin-top: 6rpx;
  color: #6b7280;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1.35;
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

.item-cover {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  overflow: hidden;
  background: #edf8e8;
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

.status-completed {
  color: #267b2f;
}

.status-in_progress {
  color: #d5a108;
}

.status-not_started {
  color: #d73546;
}

.status-cancelled {
  color: #ef3038;
}

.status-archived {
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
