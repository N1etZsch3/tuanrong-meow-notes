<template>
  <view class="records-page">
    <view class="records-inner">
      <view class="nav-row">
        <button class="back-button" @tap="goBack">‹</button>
        <text class="nav-title">{{ recordMeta.title }}</text>
      </view>

      <view class="empty-card">
        <image class="empty-image" :src="emptyImage" mode="aspectFit" />
        <text class="empty-title">{{ recordMeta.empty_title }}</text>
        <text class="empty-description">{{ recordMeta.empty_description }}</text>
        <button class="refresh-button" :loading="isLoading" @tap="loadRecords">刷新</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import {
  getFavoriteCats,
  getMyCheckins,
  getMyObservations,
  getMyTasks,
  type EmptyRecordPage,
} from "@/api/me";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import {
  PROFILE_RECORD_TYPES,
  type ProfileRecordType,
} from "./profile-page";
import emptyImage from "../../../素材/svg/缺省页/记录空空的.svg";

const userStore = useUserStore();
const recordType = ref<ProfileRecordType>("total_tasks");
const records = ref<EmptyRecordPage | null>(null);
const isLoading = ref(false);

const recordMeta = computed(() => PROFILE_RECORD_TYPES[recordType.value]);

async function loadRecords() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isLoading.value = true;
  try {
    if (recordType.value === "observations") {
      records.value = await getMyObservations(accessToken);
    } else if (recordType.value === "favorite_cats") {
      records.value = await getFavoriteCats(accessToken);
    } else if (recordType.value === "monthly_completed") {
      records.value = await getMyCheckins(accessToken);
    } else {
      records.value = await getMyTasks(accessToken);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "记录加载失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isLoading.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

onLoad((options) => {
  const type = String(options?.type || "");
  if (type in PROFILE_RECORD_TYPES) {
    recordType.value = type as ProfileRecordType;
  }
  void loadRecords();
});
</script>

<style scoped>
.records-page {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfcfb 0%, #f5faef 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.records-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: 74rpx 38rpx calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #ffffff;
  color: #2f8037;
  font-size: 58rpx;
  line-height: 54rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.1);
}

.back-button::after,
.refresh-button::after {
  border: 0;
}

.nav-title {
  color: #171b22;
  font-size: 42rpx;
  font-weight: 900;
}

.empty-card {
  margin-top: 48rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
  padding: 56rpx 36rpx 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-image {
  width: 220rpx;
  height: 180rpx;
}

.empty-title {
  margin-top: 26rpx;
  color: #23272e;
  font-size: 32rpx;
  font-weight: 900;
}

.empty-description {
  margin-top: 16rpx;
  color: #6f7780;
  font-size: 25rpx;
  line-height: 1.5;
}

.refresh-button {
  height: 78rpx;
  margin-top: 34rpx;
  padding: 0 52rpx;
  border-radius: 24rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
}
</style>
