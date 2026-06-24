const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_AMAP_WEB_KEY = "replace-with-amap-web-key";
const DEFAULT_AMAP_SECURITY_JS_CODE = "replace-with-amap-security-js-code";

export function normalizeApiBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

export const appEnv = {
  apiBaseUrl: normalizeApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL,
  ),
  amapWebKey: import.meta.env.VITE_AMAP_WEB_KEY || DEFAULT_AMAP_WEB_KEY,
  amapSecurityJsCode:
    import.meta.env.VITE_AMAP_SECURITY_JS_CODE ||
    DEFAULT_AMAP_SECURITY_JS_CODE,
  mode: import.meta.env.MODE,
};
