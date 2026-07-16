<template>
  <view class="tasks-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="task-inner">
      <view class="task-fixed">
        <view class="page-title">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="title-copy">
            <view class="title-row">
              <text class="title-text">任务</text>
              <image class="title-icon" :src="pawIcon" mode="aspectFit" />
            </view>
            <text class="title-subtitle">暑假投喂安排</text>
          </view>
        </view>

        <view class="search-box">
          <text class="search-icon">⌕</text>
          <input
            v-model="searchKeyword"
            class="search-input"
            confirm-type="search"
            placeholder="搜索任务 / 喂食点 / 位置"
            placeholder-class="search-placeholder"
            @confirm="handleSearchConfirm"
          />
          <button class="search-button" @tap="handleSearchConfirm">搜索</button>
        </view>

        <view class="filter-card">
          <picker
            class="filter-picker"
            :range="taskTypeOptions"
            range-key="label"
            :value="selectedTaskTypeIndex"
            @tap="openPicker('task_type')"
            @cancel="closePicker"
            @change="handleTaskTypeChange"
          >
            <view class="filter-control">
              <text class="picker-caption">任务类型</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedTaskTypeLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'task_type' }"
                  :src="filterArrowIcon"
                  mode="aspectFit"
                />
              </view>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="taskStatusOptions"
            range-key="label"
            :value="selectedTaskStatusIndex"
            @tap="openPicker('status')"
            @cancel="closePicker"
            @change="handleTaskStatusChange"
          >
            <view class="filter-control">
              <text class="picker-caption">任务状态</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedTaskStatusLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'status' }"
                  :src="filterArrowIcon"
                  mode="aspectFit"
                />
              </view>
            </view>
          </picker>
          <picker
            class="filter-picker"
            :range="dateFilterOptions"
            range-key="label"
            :value="selectedDateFilterIndex"
            @tap="openPicker('date')"
            @cancel="closePicker"
            @change="handleDateFilterChange"
          >
            <view class="filter-control">
              <text class="picker-caption">日期</text>
              <view class="picker-shell">
                <text class="picker-value">{{ selectedDateFilterLabel }}</text>
                <image
                  class="picker-arrow-icon"
                  :class="{ 'is-open': activePicker === 'date' }"
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
          <picker
            v-if="selectedDateFilter === 'specific'"
            class="specific-date-picker"
            mode="date"
            :value="selectedSpecificDate"
            @change="handleSpecificDateChange"
          >
            <view class="specific-date-control">
              <text>特定日期：{{ formatTaskDate(selectedSpecificDate) }}</text>
              <text class="specific-date-action">更改</text>
            </view>
          </picker>
        </view>
      </view>

      <scroll-view
        class="task-scroll"
        scroll-y
        :show-scrollbar="false"
        lower-threshold="140"
        @scrolltolower="loadMore"
      >
        <view class="task-list-body">
        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载投喂任务</text>
          <text class="state-copy">稍等一下，任务列表马上就好。</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">任务加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
        </view>

        <view v-else-if="tasks.length" class="task-list">
          <view
            v-for="task in tasks"
            :key="task.task_id"
            class="task-card"
            hover-class="task-card-hover"
            @tap="goDetail(task.task_id)"
          >
            <view class="task-image-wrap">
              <image
                v-if="task.cover_photo_url"
                class="task-image"
                :src="task.cover_photo_url"
                mode="aspectFill"
              />
              <view v-else class="task-image-placeholder">
                <image class="placeholder-icon" :src="taskIcon" mode="aspectFit" />
              </view>
            </view>
            <view class="task-main">
              <view class="task-head">
                <text class="task-title">{{ task.title }}</text>
                <text class="task-status" :class="taskStatusClass(task)">{{ getTaskListStatusLabel(task) }}</text>
              </view>
              <text class="task-desc">{{ task.description }}</text>
              <scroll-view
                class="execution-strip"
                scroll-x
                :show-scrollbar="false"
                @tap.stop
              >
                <view class="execution-row">
                  <button
                    v-for="execution in displayExecutions(task)"
                    :key="execution.execution_date_id"
                    class="execution-card"
                    :class="getExecutionDisplayClass(execution)"
                    hover-class="execution-card-hover"
                    @tap.stop="goExecutionDetail(task.task_id, execution.execution_date_id)"
                  >
                    <text class="execution-date">{{ formatTaskDate(execution.execute_date) }}</text>
                    <text class="execution-label">{{ getExecutionDisplayLabel(execution) }}</text>
                  </button>
                </view>
              </scroll-view>
            </view>
          </view>

          <view class="list-footer">
            <text v-if="isLoadingMore" class="list-footer-text">正在加载更多任务...</text>
            <text v-else-if="!hasMore" class="list-footer-text">已展示全部 {{ totalTasks }} 个任务</text>
          </view>
        </view>

        <view v-else class="state-box">
          <text class="state-title">暂无投喂任务</text>
          <text class="state-copy">发布后的喂食点会显示在这里和地图上。</text>
        </view>
      </view>
      </scroll-view>
    </view>
    <button
      v-if="userStore.isAdmin"
      class="floating-add admin-floating-add"
      hover-class="button-hover"
      @tap="goCreateTask"
    >
      新增任务
    </button>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { getTasks, type TaskExecutionDto, type TaskListItemDto, type TaskListQuery, type TaskListResponse } from "@/api/tasks";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import {
  buildTaskDateFilterQuery,
  formatTaskDate,
  formatLocalDate,
  getExecutionDisplayLabel,
  getExecutionDisplayTone,
  getTaskListStatusLabel,
  getTaskStatusTone,
  type TaskDateFilterValue,
} from "@/pages/tasks/task-page";
import {
  getCachedTaskList,
  setCachedTaskList,
} from "@/pages/tasks/task-list-cache";

import taskIcon from "../../../素材/png/地图点/日常任务.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

import filterArrowIcon from "../../../素材/png/地图点/箭头.png";
import clearFilterIcon from "../../../素材/svg/猫咪库/删除.svg";

type LoadState = "idle" | "loading" | "ready" | "error";
type PickerKind = "task_type" | "status" | "date" | "";
type PickerChangeEvent = { detail: { value: string | number } };
type DatePickerChangeEvent = { detail: { value: string } };

// 默认列表隐藏「已归档」「已取消」父任务：默认只查进行中 + 已完成。
// 「未开始/进行中/已完成」筛选走子任务展示状态 execution_display_status；
// 「已归档/已取消」筛选走父任务 status（后端 display status 永不产出 archived，
// 旧实现选「已归档」会得到空列表，这里改为按父 status 查询修复该问题）。
const DEFAULT_PARENT_STATUS_QUERY = "in_progress,completed";
const PARENT_STATUS_FILTER_VALUES = ["archived", "cancelled"] as const;
const PAGE_SIZE = 10;
const taskTypeOptions = [
  { label: "全部", value: "" },
  { label: "暑假投喂", value: "feeding" },
] as const;
const taskStatusOptions = [
  { label: "全部", value: "" },
  { label: "未开始", value: "not_started" },
  { label: "进行中", value: "in_progress" },
  { label: "已完成", value: "completed" },
  { label: "已取消", value: "cancelled" },
  { label: "已归档", value: "archived" },
] as const;
const dateFilterOptions = [
  { label: "全部", value: "" },
  { label: "本日", value: "today" },
  { label: "本周", value: "week" },
  { label: "本月", value: "month" },
  { label: "特定日期", value: "specific" },
] as const;

const userStore = useUserStore();
const tasks = ref<TaskListItemDto[]>([]);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const searchKeyword = ref("");
const selectedTaskType = ref("");
const selectedTaskStatus = ref("");
const selectedDateFilter = ref<TaskDateFilterValue>("");
const selectedSpecificDate = ref(formatLocalDate(new Date()));
const activePicker = ref<PickerKind>("");
const currentPage = ref(0);
const totalTasks = ref(0);
const hasMore = ref(false);
const isLoadingMore = ref(false);

const selectedTaskTypeIndex = computed(() =>
  Math.max(
    taskTypeOptions.findIndex((option) => option.value === selectedTaskType.value),
    0,
  ),
);
const selectedTaskStatusIndex = computed(() =>
  Math.max(
    taskStatusOptions.findIndex((option) => option.value === selectedTaskStatus.value),
    0,
  ),
);
const selectedDateFilterIndex = computed(() =>
  Math.max(
    dateFilterOptions.findIndex((option) => option.value === selectedDateFilter.value),
    0,
  ),
);
const selectedTaskTypeLabel = computed(
  () => taskTypeOptions[selectedTaskTypeIndex.value]?.label || taskTypeOptions[0].label,
);
const selectedTaskStatusLabel = computed(
  () => taskStatusOptions[selectedTaskStatusIndex.value]?.label || taskStatusOptions[0].label,
);
const selectedDateFilterLabel = computed(() => {
  if (selectedDateFilter.value === "specific") {
    return selectedSpecificDate.value ? formatTaskDate(selectedSpecificDate.value) : "特定日期";
  }
  return dateFilterOptions[selectedDateFilterIndex.value]?.label || dateFilterOptions[0].label;
});

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function buildTaskListQuery(page = 1): TaskListQuery {
  const dateQuery = buildTaskDateFilterQuery(
    selectedDateFilter.value,
    selectedSpecificDate.value,
  );
  // 「已归档」「已取消」→ 父任务 status；其余（未开始/进行中/已完成）→ 子任务展示状态。
  const isParentStatusFilter = (
    PARENT_STATUS_FILTER_VALUES as readonly string[]
  ).includes(selectedTaskStatus.value);
  const statusQuery = isParentStatusFilter
    ? selectedTaskStatus.value
    : DEFAULT_PARENT_STATUS_QUERY;
  const executionDisplayStatus = isParentStatusFilter ? "" : selectedTaskStatus.value;
  return {
    task_type: selectedTaskType.value
      ? (selectedTaskType.value as TaskListQuery["task_type"])
      : undefined,
    status: statusQuery,
    execution_display_status: executionDisplayStatus,
    keyword: searchKeyword.value.trim(),
    ...dateQuery,
    page,
    page_size: PAGE_SIZE,
  };
}

function applyFirstPage(data: TaskListResponse) {
  tasks.value = data.items;
  currentPage.value = data.page;
  totalTasks.value = data.total;
  hasMore.value = data.has_more;
}

async function fetchTasks(
  token: string,
  query: TaskListQuery,
  options: { silent?: boolean } = {},
) {
  if (!options.silent) {
    loadState.value = "loading";
  }
  try {
    const data = await getTasks(token, query);
    applyFirstPage(data);
    setCachedTaskList(query, data);
    loadState.value = "ready";
  } catch (error) {
    if (options.silent) {
      return;
    }
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

async function loadMore() {
  if (isLoadingMore.value || loadState.value !== "ready" || !hasMore.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isLoadingMore.value = true;
  try {
    const query = buildTaskListQuery(currentPage.value + 1);
    const data = await getTasks(token, query);
    const existingIds = new Set(tasks.value.map((task) => task.task_id));
    tasks.value = [
      ...tasks.value,
      ...data.items.filter((task) => !existingIds.has(task.task_id)),
    ];
    currentPage.value = data.page;
    totalTasks.value = data.total;
    hasMore.value = data.has_more;
  } catch {
    // 加载更多失败保持已加载内容，静默处理（用户可继续下拉重试）。
  } finally {
    isLoadingMore.value = false;
  }
}

async function loadTasks(options: { force?: boolean } = {}) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  const query = buildTaskListQuery();
  if (!options.force) {
    const cached = getCachedTaskList(query);
    if (cached) {
      applyFirstPage(cached);
      loadState.value = "ready";
      void fetchTasks(token, query, { silent: true });
      return;
    }
  }

  await fetchTasks(token, query);
}

function handleSearchConfirm() {
  void loadTasks({ force: true });
}

function goBack() {
  uni.navigateBack();
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

function handleTaskTypeChange(event: PickerChangeEvent) {
  selectedTaskType.value = taskTypeOptions[pickerIndex(event)]?.value || "";
  closePicker();
  void loadTasks({ force: true });
}

function handleTaskStatusChange(event: PickerChangeEvent) {
  selectedTaskStatus.value = taskStatusOptions[pickerIndex(event)]?.value || "";
  closePicker();
  void loadTasks({ force: true });
}

function handleDateFilterChange(event: PickerChangeEvent) {
  selectedDateFilter.value = (dateFilterOptions[pickerIndex(event)]?.value ||
    "") as TaskDateFilterValue;
  closePicker();
  void loadTasks({ force: true });
}

function handleSpecificDateChange(event: DatePickerChangeEvent) {
  selectedSpecificDate.value = event.detail.value;
  void loadTasks({ force: true });
}

function clearFilters() {
  searchKeyword.value = "";
  selectedTaskType.value = "";
  selectedTaskStatus.value = "";
  selectedDateFilter.value = "";
  selectedSpecificDate.value = formatLocalDate(new Date());
  closePicker();
  void loadTasks({ force: true });
}

function taskStatusClass(task: TaskListItemDto): string {
  const tone = getTaskStatusTone(task);
  if (tone === "completed") {
    return "task-status-completed";
  }
  if (tone === "in_progress") {
    return "task-status-in-progress";
  }
  if (tone === "cancelled") {
    return "task-status-cancelled";
  }
  if (tone === "archived") {
    return "task-status-archived";
  }
  return "task-status-default";
}

function displayExecutions(task: TaskListItemDto): TaskExecutionDto[] {
  const executions = task.display_executions?.length
    ? task.display_executions
    : [task.current_execution || task.next_execution].filter(Boolean);
  return executions.filter((execution): execution is TaskExecutionDto => Boolean(execution));
}

function getExecutionDisplayClass(execution: TaskExecutionDto): string {
  return `execution-card-${getExecutionDisplayTone(execution)}`;
}

function goDetail(taskId: string) {
  uni.navigateTo({ url: `/pages/tasks/detail?task_id=${taskId}` });
}

function goExecutionDetail(taskId: string, executionDateId: string) {
  uni.navigateTo({
    url: `/pages/tasks/detail?task_id=${taskId}&execution_date_id=${executionDateId}`,
  });
}

function goCreateTask() {
  uni.navigateTo({ url: "/pages/admin/tasks/create" });
}

onShow(() => {
  void loadTasks();
});
</script>

<style scoped>
.tasks-page {
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

.task-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 28rpx;
}

.task-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 36rpx);
  display: flex;
  flex-direction: column;
}

.task-fixed {
  flex: 0 0 auto;
}

.task-list-body {
  padding-bottom: 24rpx;
}

.page-title {
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

.title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
}

.title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.search-button::after,
.back-button::after,
.clear-filter-button::after,
.execution-card::after,
.floating-add::after {
  border: 0;
}

.search-box,
.filter-card,
.task-card,
.state-box {
  box-sizing: border-box;
  border: 2rpx solid rgba(197, 230, 193, 0.78);
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
}

.search-box {
  min-height: 72rpx;
  margin-top: 30rpx;
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
.floating-add,
.clear-filter-button {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
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

.floating-add {
  position: fixed;
  z-index: 5;
  right: 34rpx;
  bottom: calc(env(safe-area-inset-bottom) + 34rpx);
  width: 168rpx;
  height: 74rpx;
  border-radius: 26rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 74rpx;
  text-align: center;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.filter-card {
  margin-top: 26rpx;
  border-radius: 26rpx;
  padding: 20rpx 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 76rpx;
  align-items: end;
  gap: 10rpx;
}

.filter-picker,
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
  font-size: 20rpx;
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

.specific-date-picker {
  grid-column: 1 / -1;
}

.specific-date-control {
  box-sizing: border-box;
  min-height: 54rpx;
  border: 2rpx dashed rgba(40, 124, 49, 0.28);
  border-radius: 18rpx;
  padding: 0 18rpx;
  background: rgba(255, 255, 255, 0.72);
  color: #287c31;
  font-size: 22rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.specific-date-action {
  color: #6b7280;
  font-size: 20rpx;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.list-footer {
  padding: 28rpx 0 8rpx;
  text-align: center;
}

.list-footer-text {
  color: #8b929a;
  font-size: 22rpx;
  font-weight: 700;
}

.task-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 206rpx;
  margin: 0;
  padding: 20rpx;
  border: 0;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.1);
  color: #111827;
  display: grid;
  grid-template-columns: 152rpx minmax(0, 1fr);
  gap: 20rpx;
  text-align: left;
}

.task-card-hover,
.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.task-image-wrap,
.task-image,
.task-image-placeholder {
  width: 152rpx;
  height: 152rpx;
  border-radius: 22rpx;
  overflow: hidden;
}

.task-image-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 86rpx;
  height: 86rpx;
}

.task-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.task-head {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.task-title {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.25;
}

.task-status {
  flex-shrink: 0;
  padding: 7rpx 12rpx;
  border-radius: 12rpx;
  font-size: 20rpx;
  font-weight: 900;
}

.task-status-completed {
  background: #e6f6e4;
  color: #238033;
}

.task-status-in-progress {
  background: #fff4cc;
  color: #a66f00;
}

.task-status-cancelled {
  background: #ffe7eb;
  color: #d73546;
}

.task-status-archived {
  background: #edf4ff;
  color: #2276ff;
}

.task-status-default {
  background: #edf4ff;
  color: #2276ff;
}

.task-desc {
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.4;
}

.task-desc {
  color: #4b5563;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.execution-strip {
  width: 100%;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.execution-row {
  display: flex;
  gap: 10rpx;
}

.execution-card {
  box-sizing: border-box;
  min-width: 126rpx;
  height: 62rpx;
  margin: 0;
  padding: 7rpx 14rpx;
  border: 0;
  border-radius: 12rpx;
  text-align: left;
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  gap: 4rpx;
  flex-shrink: 0;
}

.execution-date,
.execution-label {
  display: block;
  overflow: hidden;
  font-weight: 900;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.execution-date {
  font-size: 19rpx;
}

.execution-label {
  font-size: 17rpx;
}

.execution-card-not_started {
  background: #ffe7eb;
  color: #d73546;
}

.execution-card-in_progress {
  background: #fff4cc;
  color: #a66f00;
}

.execution-card-completed {
  background: #e6f6e4;
  color: #238033;
}

.execution-card-cancelled {
  background: #e5e7eb;
  color: #667085;
}

.execution-card-default {
  background: #edf4ff;
  color: #2276ff;
}

.execution-card-hover {
  opacity: 0.86;
}

.state-box {
  box-sizing: border-box;
  padding: 46rpx 34rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.08);
}

.state-title,
.state-copy {
  display: block;
}

.state-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 14rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.5;
}
</style>
