import { appEnv } from "@/config/app-env";
import { API_ENDPOINTS } from "@/api/routes";
import {
  ApiBusinessError,
  ApiHttpError,
  ApiNetworkError,
  buildRequestUrl,
  createAuthorizationHeader,
} from "@/services/request";
import type { ApiResponse } from "@/types/api";

export interface UploadedImageAsset {
  asset_id: string;
  usage_type?: string;
  owner_type?: string | null;
  owner_id?: string | null;
  default_url: string;
  default_thumb_url: string | null;
  created_at?: string;
}

export interface UploadImageOptions {
  usage_type: string;
  owner_type?: string;
  owner_id?: string;
  visibility?: "private" | "internal" | "public";
  caption?: string;
}

export function buildFileAssetContentUrl(
  assetId: string,
  scene: string,
  variantKey?: string,
): string {
  const path = API_ENDPOINTS.files.assetContent(assetId, {
    scene,
    variant_key: variantKey,
  });
  return buildRequestUrl(appEnv.apiBaseUrl, path);
}

function compactFormData(data: UploadImageOptions): Record<string, string> {
  return Object.fromEntries(
    Object.entries(data).filter(([, value]) => value !== undefined && value !== ""),
  ) as Record<string, string>;
}

function parseUploadResponse<T>(data: unknown): ApiResponse<T> {
  if (typeof data === "string") {
    return JSON.parse(data) as ApiResponse<T>;
  }

  return data as ApiResponse<T>;
}

export function uploadImage(
  accessToken: string,
  filePath: string,
  options: UploadImageOptions,
): Promise<UploadedImageAsset> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildRequestUrl(appEnv.apiBaseUrl, API_ENDPOINTS.files.images),
      filePath,
      name: "file",
      header: createAuthorizationHeader(accessToken),
      formData: compactFormData(options),
      success: (result) => {
        const response = parseUploadResponse<UploadedImageAsset>(result.data);
        if (result.statusCode < 200 || result.statusCode >= 300) {
          if (typeof response?.code === "number") {
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

          reject(new ApiHttpError(result.statusCode));
          return;
        }

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
