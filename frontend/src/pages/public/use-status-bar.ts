import { onMounted, ref } from "vue";

// Status-bar height (px) reported by the platform, exposed as an rpx-safe px value.
// Pages bind this into the `--status-bar-height` CSS variable so the fixed top bar
// clears the notch / capsule area consistently across screen sizes, without relying
// on env(safe-area-inset-top) which is unreliable on some mini-program devices.
export function useStatusBarHeight() {
  const statusBarHeight = ref(0);

  onMounted(() => {
    try {
      const info = uni.getSystemInfoSync();
      statusBarHeight.value =
        typeof info.statusBarHeight === "number" ? info.statusBarHeight : 0;
    } catch {
      statusBarHeight.value = 0;
    }
  });

  return { statusBarHeight };
}
