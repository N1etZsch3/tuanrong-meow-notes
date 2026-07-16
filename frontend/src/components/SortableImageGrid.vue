<template>
  <view class="sortable-image-grid-wrap">
    <view class="sortable-image-grid">
      <view
        v-for="(item, index) in images"
        :key="item.key"
        class="sortable-image-card"
        :class="{ 'is-dragging': draggingKey === item.key }"
      >
        <image class="sortable-image-thumb" :src="item.url" mode="aspectFill" />
        <text v-if="index === 0" class="sortable-image-cover">{{ coverLabel }}</text>
        <view
          v-if="!disabled"
          class="sortable-image-handle"
          @longpress="beginDrag(index)"
          @touchmove.stop.prevent="handleDragMove"
          @touchend="finishDrag"
          @touchcancel="finishDrag"
        >
          ≡
        </view>
        <button
          v-if="!disabled"
          class="sortable-image-remove"
          hover-class="button-hover"
          @longpress.stop="ignoreRemoveLongPress"
          @tap.stop="emit('remove', index)"
        >
          ×
        </button>
      </view>
      <button
        v-if="showAdd && canAdd"
        class="sortable-image-add"
        :loading="uploading"
        :disabled="disabled || uploading"
        hover-class="button-hover"
        @tap="emit('add')"
      >
        +
      </button>
    </view>
    <text v-if="images.length > 1 && !disabled" class="sortable-image-hint">
      长按右下角排序手柄并拖动可调整顺序，第一张将作为封面
    </text>
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, ref } from "vue";

export interface SortableImageItem {
  key: string;
  url: string;
}

interface ItemRect {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

const props = withDefaults(
  defineProps<{
    images: SortableImageItem[];
    uploading?: boolean;
    disabled?: boolean;
    showAdd?: boolean;
    limit?: number;
    coverLabel?: string;
  }>(),
  {
    uploading: false,
    disabled: false,
    showAdd: true,
    limit: 0,
    coverLabel: "封面",
  },
);

const emit = defineEmits<{
  add: [];
  remove: [index: number];
  reorder: [fromIndex: number, toIndex: number];
}>();

const component = getCurrentInstance();
const draggingIndex = ref<number | null>(null);
const draggingKey = ref("");
const itemRects = ref<ItemRect[]>([]);
const canAdd = computed(() => props.limit <= 0 || props.images.length < props.limit);

function readTouchPoint(event: Event): { clientX: number; clientY: number } | null {
  const touchEvent = event as Event & {
    touches?: Array<{ clientX?: number; clientY?: number }>;
    changedTouches?: Array<{ clientX?: number; clientY?: number }>;
  };
  const touch = touchEvent.touches?.[0] || touchEvent.changedTouches?.[0];
  const clientX = Number(touch?.clientX);
  const clientY = Number(touch?.clientY);
  if (!Number.isFinite(clientX) || !Number.isFinite(clientY)) {
    return null;
  }
  return { clientX, clientY };
}

function cacheItemRects() {
  const query = uni.createSelectorQuery();
  if (component?.proxy) {
    query.in(component.proxy);
  }
  query
    .selectAll(".sortable-image-card")
    .boundingClientRect((rects) => {
      const values = Array.isArray(rects) ? rects : [];
      itemRects.value = values
        .map((rect) => ({
          left: Number(rect.left),
          right: Number(rect.right),
          top: Number(rect.top),
          bottom: Number(rect.bottom),
        }))
        .filter((rect) =>
          [rect.left, rect.right, rect.top, rect.bottom].every(Number.isFinite),
        );
    })
    .exec();
}

function beginDrag(index: number) {
  if (props.disabled || index < 0 || index >= props.images.length) {
    return;
  }
  draggingIndex.value = index;
  draggingKey.value = props.images[index]?.key || "";
  cacheItemRects();
  if (typeof uni.vibrateShort === "function") {
    uni.vibrateShort({ type: "light" });
  }
}

function handleDragMove(event: Event) {
  if (draggingIndex.value === null) {
    return;
  }
  const point = readTouchPoint(event);
  if (!point) {
    return;
  }
  const targetIndex = itemRects.value.findIndex(
    (rect) =>
      point.clientX >= rect.left &&
      point.clientX <= rect.right &&
      point.clientY >= rect.top &&
      point.clientY <= rect.bottom,
  );
  if (targetIndex < 0 || targetIndex === draggingIndex.value) {
    return;
  }
  const fromIndex = draggingIndex.value;
  draggingIndex.value = targetIndex;
  emit("reorder", fromIndex, targetIndex);
  void nextTick(cacheItemRects);
}

function finishDrag() {
  draggingIndex.value = null;
  draggingKey.value = "";
  itemRects.value = [];
}

function ignoreRemoveLongPress() {
  // 删除按钮只响应点击，避免长按事件冒泡到排序手柄。
}
</script>

<style scoped>
.sortable-image-grid-wrap {
  margin-top: 22rpx;
}

.sortable-image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.sortable-image-card,
.sortable-image-thumb,
.sortable-image-add {
  width: 138rpx;
  height: 138rpx;
  border-radius: 24rpx;
}

.sortable-image-card {
  position: relative;
  z-index: 1;
  transition: transform 140ms ease, opacity 140ms ease, box-shadow 140ms ease;
}

.sortable-image-card.is-dragging {
  z-index: 3;
  opacity: 0.72;
  transform: scale(1.06);
  box-shadow: 0 16rpx 34rpx rgba(17, 24, 39, 0.24);
}

.sortable-image-thumb {
  display: block;
  background: #edf3ea;
}

.sortable-image-cover {
  position: absolute;
  left: 8rpx;
  bottom: 8rpx;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(40, 124, 49, 0.9);
  color: #ffffff;
  font-size: 19rpx;
  font-weight: 900;
  line-height: 1;
}

.sortable-image-handle {
  position: absolute;
  z-index: 4;
  right: 8rpx;
  bottom: 8rpx;
  width: 42rpx;
  height: 42rpx;
  border-radius: 12rpx;
  background: rgba(17, 24, 39, 0.7);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 38rpx;
  text-align: center;
}

.sortable-image-remove {
  position: absolute;
  z-index: 4;
  top: -14rpx;
  right: -14rpx;
  width: 46rpx;
  height: 46rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(17, 24, 39, 0.76);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 42rpx;
}

.sortable-image-remove::after,
.sortable-image-add::after {
  border: 0;
}

.sortable-image-add {
  margin: 0;
  padding: 0;
  border: 2rpx dashed rgba(40, 124, 49, 0.5);
  background: #f4fbef;
  color: #287c31;
  font-size: 58rpx;
  font-weight: 700;
  line-height: 134rpx;
}

.sortable-image-hint {
  display: block;
  margin-top: 16rpx;
  color: #6b7280;
  font-size: 21rpx;
  font-weight: 700;
  line-height: 1.4;
}
</style>
