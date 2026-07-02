export const DEFAULT_LOCAL_API_BASE_URL = "http://localhost:8000/api/v1";

export interface FrontendEnv {
  VITE_API_BASE_URL?: string;
  VITE_AMAP_WEB_KEY?: string;
  VITE_AMAP_SECURITY_JS_CODE?: string;
  MODE?: string;
  DEV?: boolean;
  PROD?: boolean;
}

export function normalizeApiBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

function isLocalApiBaseUrl(url: string): boolean {
  return /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?(?:\/|$)/i.test(
    url,
  );
}

export function resolveApiBaseUrl(env: FrontendEnv): string {
  const configuredApiBaseUrl = env.VITE_API_BASE_URL?.trim();

  if (configuredApiBaseUrl) {
    const normalizedApiBaseUrl = normalizeApiBaseUrl(configuredApiBaseUrl);

    if (env.PROD && isLocalApiBaseUrl(normalizedApiBaseUrl)) {
      throw new Error(
        "生产构建不能使用本地 API 地址，请将 VITE_API_BASE_URL 配置为 HTTPS 域名地址。",
      );
    }

    return normalizedApiBaseUrl;
  }

  if (env.PROD) {
    throw new Error(
      "生产构建缺少 VITE_API_BASE_URL，请在 frontend/.env.production 或构建环境中配置 HTTPS API 域名，例如 https://your-domain.example.com/api/v1。",
    );
  }

  return DEFAULT_LOCAL_API_BASE_URL;
}
