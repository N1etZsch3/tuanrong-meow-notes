<template>
  <view class="title-identity-name" :class="`title-identity-name--${size}`">
    <image
      v-if="definition"
      class="title-identity-name__shield"
      :src="TITLE_SHIELD_ASSETS[definition.shield_asset]"
      mode="aspectFit"
    />
    <text
      class="title-identity-name__text"
      :style="{ color: definition?.name_color || fallbackColor }"
    >{{ displayText }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { TITLE_SHIELD_ASSETS } from "@/components/title-shield-assets";
import { getTitleDefinition } from "@/constants/titles";

const props = withDefaults(
  defineProps<{
    name?: string | null;
    title?: string | null;
    display?: "name" | "title";
    size?: "list" | "profile" | "detail";
    fallbackName?: string;
    fallbackColor?: string;
  }>(),
  {
    name: "",
    title: null,
    display: "name",
    size: "list",
    fallbackName: "未命名成员",
    fallbackColor: "#111827",
  },
);

const definition = computed(() => getTitleDefinition(props.title));
const displayText = computed(() => {
  if (props.display === "title") {
    return definition.value?.label || "";
  }
  return props.name || props.fallbackName;
});
</script>

<style scoped>
.title-identity-name {
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.title-identity-name__shield {
  width: 30rpx;
  height: 30rpx;
  flex: 0 0 auto;
}

.title-identity-name__text {
  min-width: 0;
  overflow: hidden;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-identity-name--profile .title-identity-name__shield {
  width: 32rpx;
  height: 32rpx;
}

.title-identity-name--profile .title-identity-name__text {
  font-size: 36rpx;
}

.title-identity-name--detail {
  width: auto;
  justify-content: center;
}

.title-identity-name--detail .title-identity-name__shield {
  width: 34rpx;
  height: 34rpx;
}

.title-identity-name--detail .title-identity-name__text {
  font-size: 32rpx;
}
</style>
