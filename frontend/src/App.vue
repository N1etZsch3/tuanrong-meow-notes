<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
onLaunch(() => {
  console.log("App Launch");
  uni.hideTabBar();
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
