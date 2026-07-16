import { defineConfig, loadEnv } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

import { resolveApiBaseUrl } from "./src/config/api-env";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");

  // Mini-program dev (`uni -p mp-weixin`) runs `vite build --watch`, so
  // `command === "build"` is NOT a production signal; `mode` is.
  const isProductionBuild = mode === "production";

  resolveApiBaseUrl({
    VITE_API_BASE_URL: env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL,
    PROD: isProductionBuild,
    DEV: !isProductionBuild,
  });

  return {
    publicDir: false,
    plugins: [uni()],
  };
});
