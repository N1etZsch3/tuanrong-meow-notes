<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { startUserLocationPreload } from "@/services/user-location";

onLaunch(() => {
  console.log("App Launch");
  startUserLocationPreload();
});
onShow(() => {
  console.log("App Show");
});
onHide(() => {
  console.log("App Hide");
});
</script>

<style>
html,
body,
#app,
uni-page-body {
  height: 100%;
  overflow: hidden;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

page {
  --catmap-page-title-top: 92rpx;
  --catmap-page-title-side: 42rpx;
  --catmap-page-title-gap: 14rpx;
  --catmap-page-title-font-size: 52rpx;
  --catmap-page-title-icon-size: 48rpx;
  --catmap-page-title-subtitle-margin: 14rpx;
  --catmap-page-title-subtitle-size: 24rpx;

  height: 100%;
  overflow: hidden;
  background: #f6faf0;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

view,
text,
input,
textarea,
button,
picker,
navigator {
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}
</style>
