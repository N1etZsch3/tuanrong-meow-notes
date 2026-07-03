<template>
  <view
    v-if="visible && activeUrl"
    class="image-preview-modal"
    @touchmove.stop.prevent
  >
    <view class="image-preview-backdrop" @tap="close" />
    <view class="image-preview-toolbar">
      <text class="image-preview-count">{{ activeIndex + 1 }} / {{ safeImages.length }}</text>
    </view>

    <movable-area class="image-preview-area" :style="imageAreaStyle">
      <movable-view
        :key="activeUrl"
        class="image-preview-movable"
        direction="all"
        :scale="true"
        :scale-min="1"
        :scale-max="4"
        :scale-value="1"
        :x="0"
        :y="0"
        @tap.stop
      >
        <image
          class="image-preview-image"
          :src="activeUrl"
          mode="aspectFit"
          @load="handleImageLoad"
        />
      </movable-view>
    </movable-area>

    <button
      v-if="safeImages.length > 1"
      class="image-preview-nav image-preview-prev"
      hover-class="image-preview-button-hover"
      @tap.stop="showPrevious"
    >
      ‹
    </button>
    <button
      v-if="safeImages.length > 1"
      class="image-preview-nav image-preview-next"
      hover-class="image-preview-button-hover"
      @tap.stop="showNext"
    >
      ›
    </button>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    visible: boolean;
    images: string[];
    currentIndex?: number;
  }>(),
  {
    currentIndex: 0,
  },
);

const emit = defineEmits<{
  close: [];
  change: [index: number];
}>();

const systemInfo = uni.getSystemInfoSync();
const viewportSize = {
  width: systemInfo.windowWidth || 375,
  height: systemInfo.windowHeight || 667,
};
const imageNaturalSize = ref<{ width: number; height: number } | null>(null);
const safeImages = computed(() => props.images.filter((url) => Boolean(url)));
const activeIndex = computed(() => {
  if (!safeImages.value.length) {
    return 0;
  }
  return Math.min(Math.max(props.currentIndex, 0), safeImages.value.length - 1);
});
const activeUrl = computed(() => safeImages.value[activeIndex.value] || "");
const imageAreaStyle = computed(() => {
  const naturalSize = imageNaturalSize.value;
  if (!naturalSize?.width || !naturalSize.height) {
    return "left:0;top:0;width:100%;height:100%;";
  }

  const imageRatio = naturalSize.width / naturalSize.height;
  const viewportRatio = viewportSize.width / viewportSize.height;
  if (imageRatio >= viewportRatio) {
    const height = viewportSize.width / imageRatio;
    const top = (viewportSize.height - height) / 2;
    return `left:0px;top:${top}px;width:${viewportSize.width}px;height:${height}px;`;
  }

  const width = viewportSize.height * imageRatio;
  const left = (viewportSize.width - width) / 2;
  return `left:${left}px;top:0px;width:${width}px;height:${viewportSize.height}px;`;
});

watch(activeUrl, () => {
  imageNaturalSize.value = null;
});

function handleImageLoad(event: Event) {
  const detail = (event as Event & { detail?: { width?: number; height?: number } }).detail;
  const width = Number(detail?.width);
  const height = Number(detail?.height);
  if (Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0) {
    imageNaturalSize.value = { width, height };
  }
}

function close() {
  emit("close");
}

function showPrevious() {
  if (!safeImages.value.length) {
    return;
  }
  const nextIndex =
    activeIndex.value === 0 ? safeImages.value.length - 1 : activeIndex.value - 1;
  emit("change", nextIndex);
}

function showNext() {
  if (!safeImages.value.length) {
    return;
  }
  const nextIndex =
    activeIndex.value === safeImages.value.length - 1 ? 0 : activeIndex.value + 1;
  emit("change", nextIndex);
}
</script>

<style scoped>
.image-preview-modal {
  position: fixed;
  z-index: 99;
  inset: 0;
  background: rgba(7, 13, 20, 0.92);
  overflow: hidden;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.image-preview-backdrop {
  position: absolute;
  inset: 0;
}

.image-preview-toolbar {
  position: absolute;
  z-index: 3;
  top: calc(env(safe-area-inset-top) + 170rpx);
  left: 30rpx;
  right: 30rpx;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  pointer-events: none;
}

.image-preview-count {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.image-preview-nav::after {
  border: 0;
}

.image-preview-area {
  position: absolute;
  z-index: 2;
}

.image-preview-movable {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-image {
  width: 100%;
  height: 100%;
}

.image-preview-nav {
  position: absolute;
  z-index: 3;
  top: 50%;
  width: 72rpx;
  height: 72rpx;
  margin: -36rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 58rpx;
  font-weight: 900;
  line-height: 66rpx;
}

.image-preview-prev {
  left: 24rpx;
}

.image-preview-next {
  right: 24rpx;
}

.image-preview-button-hover {
  opacity: 0.84;
  transform: translateY(2rpx);
}
</style>
