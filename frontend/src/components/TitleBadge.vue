<template>
  <view
    v-if="definition"
    class="title-badge"
    :style="{ backgroundColor: definition.tag_background, color: definition.tag_color }"
  >
    <image class="title-shield" :src="shieldAssets[definition.shield]" mode="aspectFit" />
    <text class="title-label">{{ definition.label }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { getTitleDefinition } from "@/constants/titles";
import goldShield from "../../素材/svg/头衔/盾牌-金.svg";
import greenShield from "../../素材/svg/头衔/盾牌-绿.svg";
import purpleShield from "../../素材/svg/头衔/盾牌-紫.svg";

const props = defineProps<{ title?: string | null }>();
const definition = computed(() => getTitleDefinition(props.title));
const shieldAssets = {
  gold: goldShield,
  purple: purpleShield,
  green: greenShield,
} as const;
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
