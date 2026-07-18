<template>
  <view
    v-if="definition"
    class="title-badge"
    :style="{ backgroundColor: definition.tag_background, color: definition.tag_color }"
  >
    <image
      class="title-shield"
      :src="TITLE_SHIELD_ASSETS[definition.shield_asset]"
      mode="aspectFit"
    />
    <text class="title-label">{{ definition.label }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { TITLE_SHIELD_ASSETS } from "@/components/title-shield-assets";
import { getTitleDefinition } from "@/constants/titles";

const props = defineProps<{ title?: string | null }>();
const definition = computed(() => getTitleDefinition(props.title));
</script>

<style scoped>
.title-badge {
  max-width: 100%;
  min-height: 42rpx;
  padding: 5rpx 12rpx;
  border-radius: 12rpx;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  gap: 7rpx;
  flex: 0 0 auto;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.title-shield {
  width: 28rpx;
  height: 28rpx;
  flex: 0 0 auto;
}

.title-label {
  overflow: hidden;
  font-size: 20rpx;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
