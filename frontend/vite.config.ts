import { defineConfig, loadEnv } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

import { resolveApiBaseUrl } from "./src/config/api-env";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");

  resolveApiBaseUrl({
    VITE_API_BASE_URL: env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL,
    PROD: command === "build",
    DEV: command !== "build",
  });

  return {
    publicDir: "favicon",
    plugins: [uni()],
  };
});
