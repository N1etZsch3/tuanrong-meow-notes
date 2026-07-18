<template>
  <view v-if="visible" class="title-modal-mask" @tap="emit('close')">
    <view class="title-modal" @tap.stop>
      <view class="title-modal-handle" />
      <view class="title-modal-heading">
        <view>
          <text class="title-modal-kicker">账号操作</text>
          <text class="title-modal-title">头衔管理</text>
        </view>
        <button class="title-modal-close" :disabled="pending" @tap="emit('close')">×</button>
      </view>

      <view class="title-current-row">
        <text class="title-current-label">当前头衔</text>
        <TitleBadge v-if="currentTitle" :title="currentTitle" />
        <text v-else class="title-current-empty">暂无头衔</text>
      </view>

      <picker
        mode="selector"
        :range="options"
        range-key="label"
        :value="0"
        :disabled="pending || !options.length"
        @change="emit('select', $event)"
      >
        <view class="title-operation is-primary">
          <view>
            <text class="title-operation-name">授予或变更头衔</text>
            <text class="title-operation-note">仅显示当前可用头衔</text>
          </view>
          <text class="title-operation-arrow">›</text>
        </view>
      </picker>

      <button
        v-if="canRevoke"
        class="title-operation is-revoke"
        :disabled="pending"
        @tap="emit('revoke')"
      >
        <view>
          <text class="title-operation-name">移除当前头衔</text>
          <text class="title-operation-note">释放后可授予其他成员</text>
        </view>
        <text class="title-operation-arrow">›</text>
      </button>

      <view class="title-risk-divider" />
      <button
        class="title-operation is-transfer"
        :disabled="pending"
        @tap="emit('transfer')"
      >
        <view>
          <text class="title-operation-name">转让会长</text>
          <text class="title-operation-note">同时转移超级管理员权限</text>
        </view>
        <text class="title-operation-arrow">›</text>
      </button>

      <text v-if="errorMessage" class="title-modal-error">{{ errorMessage }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import type { TitleCatalogItem } from "@/api/titles";
import TitleBadge from "@/components/TitleBadge.vue";

withDefaults(
  defineProps<{
    visible: boolean;
    currentTitle?: string | null;
    options: TitleCatalogItem[];
    canRevoke?: boolean;
    pending?: boolean;
    errorMessage?: string;
  }>(),
  {
    currentTitle: null,
    canRevoke: false,
    pending: false,
    errorMessage: "",
  },
);

const emit = defineEmits<{
  (event: "close"): void;
  (event: "select", value: { detail: { value: string | number } }): void;
  (event: "revoke"): void;
  (event: "transfer"): void;
}>();
</script>

<style scoped>
.title-modal-mask {
  position: fixed;
  z-index: 30;
  inset: 0;
  box-sizing: border-box;
  padding: 24rpx;
  background: rgba(17, 24, 39, 0.46);
  display: flex;
  align-items: flex-end;
}

.title-modal {
  box-sizing: border-box;
  width: 100%;
  padding: 16rpx 26rpx calc(env(safe-area-inset-bottom) + 28rpx);
  border: 2rpx solid rgba(207, 224, 202, 0.92);
  border-radius: 32rpx;
  background: #fbfff8;
  box-shadow: 0 -18rpx 48rpx rgba(31, 54, 34, 0.2);
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.title-modal-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 0 auto 20rpx;
  border-radius: 999rpx;
  background: #d3ddd1;
}

.title-modal-heading,
.title-current-row,
.title-operation {
  display: flex;
  align-items: center;
}

.title-modal-heading {
  justify-content: space-between;
}

.title-modal-kicker,
.title-modal-title,
.title-current-label,
.title-operation-name,
.title-operation-note,
.title-modal-error {
  display: block;
}

.title-modal-kicker {
  color: #7a857b;
  font-size: 20rpx;
  font-weight: 800;
}

.title-modal-title {
  margin-top: 4rpx;
  color: #173e20;
  font-size: 34rpx;
  font-weight: 900;
}

.title-modal-close {
  width: 54rpx;
  height: 54rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #edf3eb;
  color: #657067;
  font-size: 38rpx;
  line-height: 50rpx;
}

.title-modal-close::after,
.title-operation::after {
  border: 0;
}

.title-current-row {
  min-height: 68rpx;
  margin: 24rpx 0 18rpx;
  padding: 0 20rpx;
  justify-content: space-between;
  border-radius: 18rpx;
  background: #f0f6ec;
}

.title-current-label {
  color: #657067;
  font-size: 23rpx;
  font-weight: 800;
}

.title-current-empty {
  padding: 6rpx 14rpx;
  border-radius: 12rpx;
  background: #e3e7e3;
  color: #7f8881;
  font-size: 22rpx;
  font-weight: 800;
}

.title-operation {
  box-sizing: border-box;
  width: 100%;
  min-height: 92rpx;
  margin: 12rpx 0 0;
  padding: 14rpx 20rpx;
  justify-content: space-between;
  border: 2rpx solid #dce8d8;
  border-radius: 20rpx;
  background: #ffffff;
  color: #243129;
  text-align: left;
  line-height: 1.25;
}

.title-operation.is-primary {
  border-color: #93c78f;
  background: #edf8e9;
}

.title-operation.is-revoke {
  color: #8d5524;
}

.title-operation.is-transfer {
  border-color: #edc7c1;
  background: #fff8f6;
  color: #a43d35;
}

.title-operation-name {
  font-size: 26rpx;
  font-weight: 900;
}

.title-operation-note {
  margin-top: 6rpx;
  color: #788279;
  font-size: 20rpx;
  font-weight: 700;
}

.title-operation-arrow {
  margin-left: 16rpx;
  font-size: 42rpx;
  font-weight: 400;
}

.title-risk-divider {
  height: 2rpx;
  margin: 20rpx 6rpx 8rpx;
  background: #e8ece7;
}

.title-modal-error {
  margin-top: 14rpx;
  color: #c34839;
  font-size: 22rpx;
  text-align: center;
}
</style>
