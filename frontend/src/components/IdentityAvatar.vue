<template>
  <view
    class="identity-avatar"
    :class="[`identity-avatar--${size}`, frameClass]"
    @tap="emit('tap')"
  >
    <image
      class="identity-avatar__image"
      :src="src"
      mode="aspectFill"
      @error="emit('error')"
    />
    <view v-if="badgeIcon" class="identity-avatar__badge" :class="badgeClass">
      <image class="identity-avatar__badge-icon" :src="badgeIcon" mode="aspectFit" />
    </view>
    <text v-if="editable" class="identity-avatar__edit">+</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import academicCapIcon from "../../素材/svg/人员管理/学士帽.svg";
import superAdminIcon from "../../素材/svg/人员管理/超级管理员.svg";

const props = withDefaults(
  defineProps<{
    src: string;
    role?: string | null;
    size?: "list" | "card" | "detail";
    editable?: boolean;
  }>(),
  {
    role: "member",
    size: "card",
    editable: false,
  },
);

const emit = defineEmits<{
  (event: "tap"): void;
  (event: "error"): void;
}>();

const normalizedRole = computed(() => {
  if (props.role === "super_admin" || props.role === "admin" || props.role === "summer_volunteer") {
    return props.role;
  }
  return "member";
});
const frameClass = computed(() => `identity-avatar--${normalizedRole.value}`);
const badgeClass = computed(() => `identity-avatar__badge--${normalizedRole.value}`);
const badgeIcon = computed(() => {
  if (normalizedRole.value === "super_admin") {
    return superAdminIcon;
  }
  if (normalizedRole.value === "admin") {
    return academicCapIcon;
  }
  return "";
});
</script>

<style scoped>
.identity-avatar {
  position: relative;
  box-sizing: border-box;
  flex: 0 0 auto;
  padding: 7rpx;
  border: 4rpx solid transparent;
  border-radius: 50%;
  box-shadow: 0 12rpx 28rpx rgba(42, 63, 43, 0.12);
}

.identity-avatar--list {
  width: 118rpx;
  height: 118rpx;
}

.identity-avatar--card {
  width: 142rpx;
  height: 142rpx;
}

.identity-avatar--detail {
  width: 184rpx;
  height: 184rpx;
  padding: 9rpx;
  border-width: 5rpx;
}

.identity-avatar--super_admin {
  border-color: #d94343;
  background: #ffe0de;
  box-shadow: 0 14rpx 32rpx rgba(190, 43, 43, 0.2);
}

.identity-avatar--admin {
  border-color: #67b663;
  background: #d9f4d5;
}

.identity-avatar--summer_volunteer {
  border-color: #e39a3b;
  background: #ffebcc;
}

.identity-avatar--member {
  border-color: #5d9fd3;
  background: #d7edff;
}

.identity-avatar__image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #ffffff;
}

.identity-avatar__badge {
  position: absolute;
  z-index: 2;
  left: -10rpx;
  top: -10rpx;
  box-sizing: border-box;
  width: 46rpx;
  height: 46rpx;
  padding: 7rpx;
  border: 3rpx solid #67b663;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 6rpx 14rpx rgba(36, 124, 50, 0.16);
}

.identity-avatar--detail .identity-avatar__badge {
  width: 54rpx;
  height: 54rpx;
  padding: 8rpx;
}

.identity-avatar__badge--super_admin {
  border-color: #d94343;
  box-shadow: 0 6rpx 16rpx rgba(190, 43, 43, 0.22);
}

.identity-avatar__badge-icon {
  display: block;
  width: 100%;
  height: 100%;
}

.identity-avatar__edit {
  position: absolute;
  z-index: 3;
  right: -2rpx;
  bottom: 4rpx;
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid #ffffff;
  border-radius: 50%;
  background: #2f8037;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  line-height: 42rpx;
  text-align: center;
}
</style>
