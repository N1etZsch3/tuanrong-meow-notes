import {
  normalizeApiBaseUrl,
  resolveApiBaseUrl,
} from "@/config/api-env";

export { normalizeApiBaseUrl, resolveApiBaseUrl };

export const appEnv = {
  apiBaseUrl: resolveApiBaseUrl(import.meta.env),
  amapWebKey: import.meta.env.VITE_AMAP_WEB_KEY || "",
  amapSecurityJsCode: import.meta.env.VITE_AMAP_SECURITY_JS_CODE || "",
  mode: import.meta.env.MODE,
};
