import { appEnv } from "@/config/app-env";
import type { ApiResponse, HttpMethod, RequestData } from "@/types/api";

type UniRequestMethod = NonNullable<UniNamespace.RequestOptions["method"]>;

export interface RequestOptions<TData extends RequestData = RequestData> {
  url: string;
  method?: HttpMethod;
  data?: TData;
  header?: Record<string, string>;
  token?: string;
  timeout?: number;
}

export class ApiBusinessError extends Error {
  constructor(
    public readonly code: number,
    message: string,
    public readonly traceId: string,
    public readonly data: unknown,
  ) {
    super(message);
    this.name = "ApiBusinessError";
  }
}

export class ApiHttpError extends Error {
  constructor(
    public readonly statusCode: number,
    message = "请求失败",
  ) {
    super(message);
    this.name = "ApiHttpError";
  }
}

export class ApiNetworkError extends Error {
  constructor(message = "网络异常，请稍后重试") {
    super(message);
    this.name = "ApiNetworkError";
  }
}

export function buildRequestUrl(baseUrl: string, path: string): string {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.replace(/^\/+/, "");

  return `${normalizedBaseUrl}/${normalizedPath}`;
}

export function createAuthorizationHeader(
  token?: string,
): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function request<TResponse, TData extends RequestData = RequestData>(
  options: RequestOptions<TData>,
): Promise<TResponse> {
  const method = (options.method || "GET") as UniRequestMethod;

  return new Promise<TResponse>((resolve, reject) => {
    uni.request({
      url: buildRequestUrl(appEnv.apiBaseUrl, options.url),
      method,
      data: options.data,
      timeout: options.timeout || 15000,
      header: {
        "Content-Type": "application/json",
        ...createAuthorizationHeader(options.token),
        ...options.header,
      },
      success: (result) => {
        if (result.statusCode < 200 || result.statusCode >= 300) {
          reject(new ApiHttpError(result.statusCode));
          return;
        }

        const response = result.data as ApiResponse<TResponse>;
        if (response.code !== 0) {
          reject(
            new ApiBusinessError(
              response.code,
              response.message,
              response.trace_id,
              response.data,
            ),
          );
          return;
        }

        resolve(response.data);
      },
      fail: (error) => {
        reject(new ApiNetworkError(error.errMsg));
      },
    });
  });
}
