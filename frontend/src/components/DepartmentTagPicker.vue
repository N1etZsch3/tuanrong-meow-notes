<template>
  <view class="dept-picker">
    <view v-if="modelValue.length" class="dept-tags">
      <view v-for="dept in modelValue" :key="dept" class="dept-tag">
        <text class="dept-tag-text">{{ dept }}</text>
        <text
          v-if="!disabled"
          class="dept-tag-remove"
          @tap.stop="removeDepartment(dept)"
        >
          ×
        </text>
      </view>
    </view>
    <text v-else class="dept-empty">{{ placeholder }}</text>

    <button
      v-if="!disabled && availableDepartments.length"
      class="dept-add"
      @tap="openDepartmentPicker"
    >
      ＋ 添加部门
    </button>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { DEPARTMENTS } from "@/constants/departments";

const props = withDefaults(
  defineProps<{
    modelValue: string[];
    disabled?: boolean;
    placeholder?: string;
  }>(),
  {
    disabled: false,
    placeholder: "请添加部门",
  },
);

const emit = defineEmits<{
  (event: "update:modelValue", value: string[]): void;
}>();

const availableDepartments = computed(() =>
  DEPARTMENTS.filter((dept) => !props.modelValue.includes(dept)),
);

function removeDepartment(dept: string) {
  emit(
    "update:modelValue",
    props.modelValue.filter((item) => item !== dept),
  );
}

function openDepartmentPicker() {
  const options = availableDepartments.value;
  if (!options.length) {
    return;
  }
  // 微信/uni 原生 action-sheet 选择未选中的部门（原生优先）
  uni.showActionSheet({
    itemList: [...options],
    success: (result) => {
      const picked = options[result.tapIndex];
      if (picked && !props.modelValue.includes(picked)) {
        emit("update:modelValue", [...props.modelValue, picked]);
      }
    },
  });
}
</script>

<style scoped>
.dept-picker {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.dept-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.dept-tag {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 10rpx 8rpx 18rpx;
  border-radius: 14rpx;
  background: #e6f6e4;
}

.dept-tag-text {
  color: #238033;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.dept-tag-remove {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: rgba(35, 128, 51, 0.16);
  color: #238033;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 34rpx;
  text-align: center;
}

.dept-empty {
  color: #9aa1ac;
  font-size: 26rpx;
  line-height: 1.4;
}

.dept-add {
  align-self: flex-start;
  margin: 0;
  padding: 0 22rpx;
  height: 60rpx;
  border: 2rpx dashed rgba(47, 128, 55, 0.5);
  border-radius: 16rpx;
  background: rgba(47, 128, 55, 0.06);
  color: #2f8037;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 56rpx;
}

.dept-add::after {
  border: 0;
}
</style>
