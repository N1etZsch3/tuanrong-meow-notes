<template>
  <view class="dept-picker" :class="{ 'is-large': size === 'large' }">
    <view class="dept-picker-row">
      <view v-if="modelValue.length" class="dept-tags">
        <view
          v-for="dept in modelValue"
          :key="dept"
          class="dept-tag"
          :style="getDepartmentTagStyle(dept)"
        >
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
        aria-label="添加部门"
        hover-class="dept-add-hover"
        @tap="openDepartmentPicker"
      >
        <text class="dept-add-icon">+</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { DEPARTMENTS, getDepartmentTagStyle } from "@/constants/departments";

const props = withDefaults(
  defineProps<{
    modelValue: string[];
    disabled?: boolean;
    placeholder?: string;
    size?: "default" | "large";
  }>(),
  {
    disabled: false,
    placeholder: "请添加部门",
    size: "default",
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
  width: 100%;
}

.dept-picker-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.dept-tags {
  min-width: 0;
  flex: 1;
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
}

.dept-tag-text {
  color: inherit;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.dept-tag-remove {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.52);
  color: inherit;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 34rpx;
  text-align: center;
}

.dept-empty {
  min-width: 0;
  flex: 1;
  color: #9aa1ac;
  font-size: 26rpx;
  line-height: 1.4;
}

.dept-add {
  box-sizing: border-box;
  flex: 0 0 auto;
  margin: 0;
  padding: 0;
  width: 58rpx;
  height: 58rpx;
  border: 2rpx dashed rgba(47, 128, 55, 0.5);
  border-radius: 50%;
  background: rgba(47, 128, 55, 0.06);
  color: #2f8037;
  line-height: 54rpx;
}

.dept-add-icon {
  display: block;
  font-size: 42rpx;
  font-weight: 500;
  line-height: 52rpx;
  text-align: center;
}

.dept-add-hover {
  background: rgba(47, 128, 55, 0.14);
}

.dept-add::after {
  border: 0;
}

.dept-picker.is-large .dept-tag {
  padding: 12rpx 14rpx 12rpx 22rpx;
  border-radius: 18rpx;
}

.dept-picker.is-large .dept-tag-text {
  font-size: 29rpx;
}

.dept-picker.is-large .dept-tag-remove {
  width: 40rpx;
  height: 40rpx;
  font-size: 34rpx;
  line-height: 40rpx;
}

.dept-picker.is-large .dept-add {
  width: 66rpx;
  height: 66rpx;
  line-height: 62rpx;
}

.dept-picker.is-large .dept-add-icon {
  font-size: 48rpx;
  line-height: 60rpx;
}
</style>
