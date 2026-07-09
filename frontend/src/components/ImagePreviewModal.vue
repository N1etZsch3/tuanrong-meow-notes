<template>
  <view
    v-if="visible && safeImages.length"
    class="image-preview-modal"
    @tap="close"
    @touchmove.stop.prevent
  >
    <view class="image-preview-toolbar">
      <text class="image-preview-count">{{ activeIndex + 1 }} / {{ safeImages.length }}</text>
    </view>

    <swiper
      class="image-preview-swiper"
      :current="activeIndex"
      :circular="safeImages.length > 1"
      :duration="260"
      @change="handleSwiperChange"
    >
      <swiper-item
        v-for="(url, index) in safeImages"
        :key="`${index}-${url}`"
        class="image-preview-item"
      >
        <movable-area
          class="image-preview-area"
          scale-area
          :style="imageAreaStyle(url)"
        >
          <movable-view
            :key="`${index}-${movableResetTokens[index] || 0}`"
            class="image-preview-movable"
            direction="all"
            :scale="true"
            :scale-min="1"
            :scale-max="4"
            :scale-value="1"
            :x="0"
            :y="0"
          >
            <image
              class="image-preview-image"
              :src="url"
              mode="aspectFit"
              @load="handleImageLoad(url, $event)"
              @tap="close"
            />
          </movable-view>
        </movable-area>
      </swiper-item>
    </swiper>
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
const imageNaturalSizes = ref<Record<string, { width: number; height: number }>>({});
const movableResetTokens = ref<Record<number, number>>({});
const safeImages = computed(() => props.images.filter((url) => Boolean(url)));
const activeIndex = computed(() => {
  if (!safeImages.value.length) {
    return 0;
  }
  return Math.min(Math.max(props.currentIndex, 0), safeImages.value.length - 1);
});

watch(activeIndex, (next, previous) => {
  if (previous === undefined || previous === next) {
    return;
  }
  // 离开某页时重挂 movable-view，把该页缩放/位移复位，下次回看从 1 倍开始
  movableResetTokens.value = {
    ...movableResetTokens.value,
    [previous]: (movableResetTokens.value[previous] || 0) + 1,
  };
});

function imageAreaStyle(url: string): string {
  const naturalSize = imageNaturalSizes.value[url];
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
}

function handleImageLoad(url: string, event: Event) {
  const detail = (event as Event & { detail?: { width?: number; height?: number } }).detail;
  const width = Number(detail?.width);
  const height = Number(detail?.height);
  if (Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0) {
    imageNaturalSizes.value = {
      ...imageNaturalSizes.value,
      [url]: { width, height },
    };
  }
}

function handleSwiperChange(event: Event) {
  const detail = (event as Event & { detail?: { current?: number } }).detail;
  const nextIndex = Number(detail?.current);
  if (!Number.isFinite(nextIndex) || nextIndex === activeIndex.value) {
    return;
  }
  emit("change", nextIndex);
}

function close() {
  emit("close");
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

.image-preview-swiper {
  position: absolute;
  z-index: 2;
  inset: 0;
  width: 100%;
  height: 100%;
}

.image-preview-item {
  position: relative;
  width: 100%;
  height: 100%;
}

.image-preview-area {
  position: absolute;
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
</style>
