<template>
  <view class="publish-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="publish-scroll" scroll-y :show-scrollbar="false">
      <view class="publish-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">发布喂食任务</text>
            <text class="nav-subtitle">创建暑假投喂任务</text>
          </view>
        </view>

        <view class="task-type-chip">
          <image class="chip-icon" :src="taskIcon" mode="aspectFit" />
          <text>喂食任务</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">1</text>
            <text class="section-title">任务标题</text>
          </view>
          <textarea
            v-model.trim="form.title"
            class="field-textarea title-textarea"
            maxlength="30"
            placeholder="请输入任务标题（如：宿舍区北侧投喂）"
            placeholder-class="placeholder"
          />
          <text class="char-count">{{ form.title.length }}/30</text>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">2</text>
            <text class="section-title">任务说明</text>
          </view>
          <textarea
            v-model.trim="form.description"
            class="field-textarea"
            maxlength="120"
            placeholder="说明本次投喂、换水、观察等事项"
            placeholder-class="placeholder"
          />
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">3</text>
            <text class="section-title">时间</text>
          </view>
          <text class="section-hint">支持多选日期，适合连续投喂</text>
          <view class="date-row">
            <view class="date-summary">
              <text>{{ dateSummary }}</text>
            </view>
            <button class="date-picker-button" hover-class="button-hover" @tap="openCalendar">
              选择日期
            </button>
          </view>
          <view v-if="form.execute_dates.length" class="date-tags">
            <button
              v-for="dateValue in form.execute_dates"
              :key="dateValue"
              class="date-tag"
              hover-class="button-hover"
              @tap="removeDate(dateValue)"
            >
              {{ formatDateText(dateValue) }} ×
            </button>
          </view>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">4</text>
            <text class="section-title">位置</text>
          </view>
          <view class="location-layout">
            <view class="map-preview">
              <text class="map-label">{{ selectedLocation?.location_name || "未选择位置" }}</text>
              <view class="map-pin">●</view>
            </view>
            <view class="location-copy">
              <text class="location-title">
                {{ selectedLocation?.location_name || "请选择任务位置" }}
              </text>
              <text class="location-detail">
                {{ selectedLocation?.location_detail || "点击地图选点插入喂食点" }}
              </text>
              <button class="outline-button" hover-class="button-hover" @tap="goLocation">
                地图选点
              </button>
            </view>
          </view>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">5</text>
            <text class="section-title">所需物资</text>
          </view>
          <input
            v-model.trim="form.required_items"
            class="field-input"
            maxlength="40"
            placeholder="默认：猫粮、水"
            placeholder-class="placeholder"
          />
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">6</text>
            <text class="section-title">任务点图片</text>
          </view>
          <view class="photo-grid">
            <image
              v-for="photo in form.photos"
              :key="photo.file_id"
              class="photo-thumb"
              :src="photo.thumbnail_url || photo.file_url"
              mode="aspectFill"
            />
            <button
              class="photo-upload"
              :loading="isUploading"
              hover-class="button-hover"
              @tap="chooseTaskPhoto"
            >
              +
            </button>
          </view>
        </view>

        <view class="form-section">
          <view class="section-title-row">
            <text class="step-badge">7</text>
            <text class="section-title">路线说明</text>
          </view>
          <textarea
            v-model.trim="form.route_instruction"
            class="field-textarea"
            maxlength="120"
            placeholder="可留空；例如：从教学楼B北侧小路进入"
            placeholder-class="placeholder"
          />
        </view>
      </view>
    </scroll-view>

    <view class="bottom-actions">
      <button class="cancel-button" hover-class="button-hover" @tap="goBack">取消</button>
      <button
        class="submit-button"
        :loading="isSubmitting"
        hover-class="button-hover"
        @tap="submitTask"
      >
        发布任务
      </button>
    </view>

    <view v-if="calendarVisible" class="calendar-overlay" @tap="cancelCalendar">
      <view class="calendar-panel" @tap.stop>
        <view class="calendar-head">
          <button
            class="calendar-nav"
            hover-class="button-hover"
            @tap="changeCalendarMonth(-1)"
          >
            ‹
          </button>
          <text class="calendar-title">{{ calendarTitle }}</text>
          <button
            class="calendar-nav"
            hover-class="button-hover"
            @tap="changeCalendarMonth(1)"
          >
            ›
          </button>
        </view>
        <view class="calendar-week-row">
          <text v-for="week in calendarWeeks" :key="week">{{ week }}</text>
        </view>
        <view class="calendar-grid">
          <button
            v-for="day in calendarDays"
            :key="day.key"
            class="calendar-day"
            :class="{
              'is-blank': day.is_blank,
              'is-disabled': day.is_disabled,
              'is-selected': isCalendarDateSelected(day.date_value),
            }"
            :disabled="day.is_blank || day.is_disabled"
            hover-class="button-hover"
            @tap="toggleCalendarDate(day.date_value)"
          >
            {{ day.label }}
          </button>
        </view>
        <view class="calendar-actions">
          <button class="calendar-cancel" hover-class="button-hover" @tap="cancelCalendar">
            取消
          </button>
          <button class="calendar-confirm" hover-class="button-hover" @tap="confirmCalendarDates">
            确定
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";

import { uploadImage } from "@/api/files";
import { publishSummerFeedingTask } from "@/api/tasks";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import {
  TASK_PUBLISH_LOCATION_STORAGE_KEY,
  buildSummerFeedingTaskPayload,
  buildUploadedTaskPhoto,
  createDefaultFeedingTaskDraft,
  formatDateText,
  formatExecutionDateSummary,
  sortUniqueDates,
  validatePublishDraft,
  type FeedingTaskDraft,
  type SelectedTaskLocation,
} from "@/pages/tasks/task-page";

import taskIcon from "../../../../素材/icon/任务.png";
import loadingBackground from "../../../../素材/加载页素材/加载页背景.jpg";

const userStore = useUserStore();
const form = reactive<FeedingTaskDraft>(createDefaultFeedingTaskDraft());
const isUploading = ref(false);
const isSubmitting = ref(false);
const selectedLocation = computed(() => form.location);
const dateSummary = computed(() => formatExecutionDateSummary(form.execute_dates));
const calendarVisible = ref(false);
const calendarDraftDates = ref<string[]>([]);
const calendarMonth = ref(new Date(2026, 6, 1));
const calendarWeeks = ["日", "一", "二", "三", "四", "五", "六"];
const CALENDAR_START_DATE = "2026-07-01";
const CALENDAR_END_DATE = "2026-09-01";

interface CalendarDay {
  key: string;
  label: string;
  date_value: string;
  is_blank: boolean;
  is_disabled: boolean;
}

const calendarTitle = computed(() => {
  const year = calendarMonth.value.getFullYear();
  const month = calendarMonth.value.getMonth() + 1;
  return `${year}年${month}月`;
});

const calendarDays = computed<CalendarDay[]>(() => {
  const year = calendarMonth.value.getFullYear();
  const month = calendarMonth.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const totalDays = new Date(year, month + 1, 0).getDate();
  const cells: CalendarDay[] = [];

  for (let index = 0; index < firstDay.getDay(); index += 1) {
    cells.push({
      key: `blank-${year}-${month}-${index}`,
      label: "",
      date_value: "",
      is_blank: true,
      is_disabled: true,
    });
  }

  for (let day = 1; day <= totalDays; day += 1) {
    const dateValue = toYmd(year, month + 1, day);
    cells.push({
      key: dateValue,
      label: String(day),
      date_value: dateValue,
      is_blank: false,
      is_disabled: dateValue < CALENDAR_START_DATE || dateValue > CALENDAR_END_DATE,
    });
  }

  return cells;
});

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

function toYmd(year: number, month: number, day: number): string {
  return [year, month, day]
    .map((item, index) => (index === 0 ? String(item) : String(item).padStart(2, "0")))
    .join("-");
}

function monthFromDateValue(value: string): Date {
  const [year, month] = value.split("-").map(Number);
  return new Date(year, month - 1, 1);
}

function openCalendar() {
  calendarDraftDates.value = [...form.execute_dates];
  calendarMonth.value = monthFromDateValue(form.execute_dates[0] || CALENDAR_START_DATE);
  calendarVisible.value = true;
}

function cancelCalendar() {
  calendarVisible.value = false;
}

function changeCalendarMonth(delta: number) {
  const current = calendarMonth.value;
  const next = new Date(current.getFullYear(), current.getMonth() + delta, 1);
  const nextValue = toYmd(next.getFullYear(), next.getMonth() + 1, 1);
  if (nextValue < "2026-07-01" || nextValue > "2026-09-01") {
    return;
  }
  calendarMonth.value = next;
}

function isCalendarDateSelected(value: string): boolean {
  return Boolean(value && calendarDraftDates.value.includes(value));
}

function toggleCalendarDate(value: string) {
  if (!value || value < CALENDAR_START_DATE || value > CALENDAR_END_DATE) {
    return;
  }

  if (calendarDraftDates.value.includes(value)) {
    calendarDraftDates.value = calendarDraftDates.value.filter((item) => item !== value);
    return;
  }

  calendarDraftDates.value = sortUniqueDates([...calendarDraftDates.value, value]);
}

function confirmCalendarDates() {
  form.execute_dates = sortUniqueDates(calendarDraftDates.value);
  calendarVisible.value = false;
}

function removeDate(value: string) {
  form.execute_dates = form.execute_dates.filter((item) => item !== value);
}

function chooseTaskPhoto() {
  uni.chooseImage({
    count: 3,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths].filter(Boolean);
      void uploadTaskPointPhotos(paths);
    },
  });
}

async function uploadTaskPointPhotos(paths: string[]) {
  const token = await getAccessToken();
  if (!token || !paths.length) {
    return;
  }

  isUploading.value = true;
  try {
    for (const path of paths) {
      const asset = await uploadImage(token, path, {
        usage_type: "map_point_scene",
        owner_type: "task",
        visibility: "internal",
        caption: "任务点图片",
      });
      form.photos = [...form.photos, buildUploadedTaskPhoto(asset)];
    }
    uni.showToast({ title: "图片已上传", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isUploading.value = false;
  }
}

async function submitTask() {
  const validation = validatePublishDraft(form);
  if (!validation.valid) {
    uni.showToast({ title: validation.message || "请完善任务信息", icon: "none" });
    return;
  }

  const token = await getAccessToken();
  if (!token || isSubmitting.value) {
    return;
  }

  isSubmitting.value = true;
  try {
    const response = await publishSummerFeedingTask(
      buildSummerFeedingTaskPayload(form),
      token,
    );
    uni.removeStorageSync(TASK_PUBLISH_LOCATION_STORAGE_KEY);
    uni.showToast({ title: "任务已发布", icon: "success" });
    uni.redirectTo({ url: `/pages/tasks/detail?task_id=${response.task_id}` });
  } catch (error) {
    const message = error instanceof Error ? error.message : "发布失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function readSelectedLocation() {
  const value = uni.getStorageSync(TASK_PUBLISH_LOCATION_STORAGE_KEY);
  if (value && typeof value === "object") {
    const location = value as SelectedTaskLocation;
    form.location = location;
    form.route_instruction = location.route_instruction || form.route_instruction;
  }
}

function goLocation() {
  uni.navigateTo({ url: "/pages/admin/tasks/location" });
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  readSelectedLocation();
});
</script>

<style scoped>
.publish-page {
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

.publish-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.publish-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 166rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.outline-button::after,
.photo-upload::after,
.date-picker-button::after,
.date-tag::after,
.calendar-nav::after,
.calendar-day::after,
.calendar-cancel::after,
.calendar-confirm::after,
.cancel-button::after,
.submit-button::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.section-title,
.section-hint,
.char-count,
.location-title,
.location-detail {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: 46rpx;
  font-weight: 900;
}

.nav-subtitle {
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 25rpx;
  font-weight: 700;
}

.task-type-chip {
  width: fit-content;
  margin-top: 34rpx;
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: #e8f5e6;
  color: #287c31;
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 25rpx;
  font-weight: 900;
}

.chip-icon {
  width: 36rpx;
  height: 36rpx;
}

.form-section {
  position: relative;
  box-sizing: border-box;
  margin-top: 28rpx;
  padding: 30rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.step-badge {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #287c31;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 40rpx;
  text-align: center;
}

.section-title {
  color: #111827;
  font-size: 31rpx;
  font-weight: 900;
}

.section-hint {
  margin: 12rpx 0 22rpx 54rpx;
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 700;
}

.field-textarea,
.field-input {
  box-sizing: border-box;
  width: 100%;
  margin-top: 24rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.35);
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #111827;
  font-size: 27rpx;
  font-weight: 700;
}

.field-textarea {
  min-height: 160rpx;
  padding: 24rpx;
  line-height: 1.5;
}

.title-textarea {
  min-height: 186rpx;
}

.field-input {
  height: 82rpx;
  padding: 0 24rpx;
}

.placeholder {
  color: #8b919b;
  font-weight: 700;
}

.char-count {
  margin-top: 10rpx;
  color: #6b7280;
  font-size: 22rpx;
  text-align: right;
}

.date-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 168rpx;
  gap: 14rpx;
}

.date-summary,
.date-picker-button {
  height: 74rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  padding: 0 22rpx;
  font-size: 24rpx;
  font-weight: 900;
}

.date-summary {
  min-width: 0;
  background: #edf8e8;
  color: #287c31;
}

.date-picker-button {
  margin: 0;
  padding: 0 22rpx;
  justify-content: center;
  border: 2rpx solid #287c31;
  color: #287c31;
  background: #ffffff;
  line-height: 70rpx;
}

.date-tags {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.date-tag {
  height: 56rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  border-radius: 16rpx;
  background: #e8f5e6;
  color: #287c31;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 56rpx;
}

.location-layout {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: 250rpx minmax(0, 1fr);
  gap: 24rpx;
  align-items: center;
}

.map-preview {
  position: relative;
  height: 220rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.68) 11rpx, transparent 1rpx),
    linear-gradient(rgba(255, 255, 255, 0.68) 11rpx, transparent 1rpx),
    #dff2d2;
  background-size: 58rpx 58rpx;
}

.map-label {
  position: absolute;
  left: 18rpx;
  right: 18rpx;
  bottom: 18rpx;
  padding: 8rpx 10rpx;
  border-radius: 12rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #2f3a2f;
  font-size: 22rpx;
  font-weight: 900;
  text-align: center;
}

.map-pin {
  position: absolute;
  left: 50%;
  top: 44%;
  width: 68rpx;
  height: 68rpx;
  margin: -34rpx 0 0 -34rpx;
  border-radius: 50%;
  background: #287c31;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 68rpx;
  text-align: center;
  box-shadow: 0 0 0 24rpx rgba(40, 124, 49, 0.16);
}

.location-title {
  color: #111827;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.35;
}

.location-detail {
  margin-top: 14rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.45;
}

.outline-button {
  width: 174rpx;
  height: 68rpx;
  margin: 22rpx 0 0;
  padding: 0;
  border: 2rpx solid #287c31;
  border-radius: 20rpx;
  background: #ffffff;
  color: #287c31;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 64rpx;
}

.photo-grid {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.photo-thumb,
.photo-upload {
  width: 150rpx;
  height: 150rpx;
  border-radius: 22rpx;
}

.photo-thumb {
  overflow: hidden;
}

.photo-upload {
  margin: 0;
  padding: 0;
  border: 2rpx dashed rgba(40, 124, 49, 0.5);
  background: #f4fbef;
  color: #287c31;
  font-size: 58rpx;
  font-weight: 700;
  line-height: 138rpx;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22rpx;
}

.calendar-overlay {
  position: fixed;
  z-index: 12;
  inset: 0;
  background: rgba(17, 24, 39, 0.42);
  display: flex;
  align-items: flex-end;
}

.calendar-panel {
  box-sizing: border-box;
  width: 100%;
  max-height: 78vh;
  padding: 30rpx 30rpx calc(env(safe-area-inset-bottom) + 28rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -18rpx 46rpx rgba(17, 24, 39, 0.18);
}

.calendar-head {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 72rpx;
  align-items: center;
}

.calendar-nav {
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #e8f5e6;
  color: #287c31;
  font-size: 44rpx;
  font-weight: 900;
  line-height: 68rpx;
}

.calendar-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
  text-align: center;
}

.calendar-week-row,
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.calendar-week-row {
  margin-top: 24rpx;
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 900;
  text-align: center;
}

.calendar-grid {
  margin-top: 18rpx;
  gap: 10rpx;
}

.calendar-day {
  width: 100%;
  height: 70rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #f5faf3;
  color: #243042;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 70rpx;
}

.calendar-day.is-blank {
  background: transparent;
}

.calendar-day.is-disabled {
  background: #f4f5f4;
  color: #b8beb7;
}

.calendar-day.is-selected {
  background: #287c31;
  color: #ffffff;
  box-shadow: 0 10rpx 22rpx rgba(40, 124, 49, 0.2);
}

.calendar-actions {
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18rpx;
}

.calendar-cancel,
.calendar-confirm {
  height: 78rpx;
  margin: 0;
  padding: 0;
  border-radius: 24rpx;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 78rpx;
}

.calendar-cancel {
  border: 2rpx solid rgba(40, 124, 49, 0.35);
  background: #ffffff;
  color: #287c31;
}

.calendar-confirm {
  border: 0;
  background: #287c31;
  color: #ffffff;
}

.cancel-button,
.submit-button {
  height: 92rpx;
  margin: 0;
  padding: 0;
  border-radius: 30rpx;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 92rpx;
}

.cancel-button {
  border: 2rpx solid #287c31;
  background: rgba(255, 255, 255, 0.96);
  color: #287c31;
}

.submit-button {
  border: 0;
  background: #287c31;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.22);
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
