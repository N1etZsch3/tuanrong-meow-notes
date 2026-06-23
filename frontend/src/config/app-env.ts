const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export function normalizeApiBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

export const appEnv = {
  apiBaseUrl: normalizeApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL,
  ),
  mode: import.meta.env.MODE,
};
