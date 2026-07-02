import {
  normalizeApiBaseUrl,
  resolveApiBaseUrl,
} from "@/config/api-env";

const DEFAULT_AMAP_WEB_KEY = "replace-with-amap-web-key";
const DEFAULT_AMAP_SECURITY_JS_CODE = "replace-with-amap-security-js-code";

export { normalizeApiBaseUrl, resolveApiBaseUrl };

export const appEnv = {
  apiBaseUrl: resolveApiBaseUrl(import.meta.env),
  amapWebKey: import.meta.env.VITE_AMAP_WEB_KEY || DEFAULT_AMAP_WEB_KEY,
  amapSecurityJsCode:
    import.meta.env.VITE_AMAP_SECURITY_JS_CODE ||
    DEFAULT_AMAP_SECURITY_JS_CODE,
  mode: import.meta.env.MODE,
};
