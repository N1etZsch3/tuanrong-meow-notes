import { appEnv } from "@/config/app-env";
import { API_ENDPOINTS } from "@/api/routes";
import {
  ApiBusinessError,
  ApiHttpError,
  ApiNetworkError,
  buildRequestUrl,
  createAuthorizationHeader,
  request,
} from "@/services/request";
import type { ApiResponse } from "@/types/api";
import { requestWechatLoginCode } from "@/services/wechat-auth";

export interface UploadedImageAsset {
  asset_id: string;
  usage_type?: string;
  owner_type?: string | null;
  owner_id?: string | null;
  default_url: string | null;
  default_thumb_url: string | null;
  security_status?: "legacy" | "pending" | "passed" | "rejected" | "failed";
  review_message?: string;
  created_at?: string;
}

export interface ApprovedImageAsset extends Omit<UploadedImageAsset, "default_url" | "security_status"> {
  default_url: string;
  security_status?: "legacy" | "passed";
}

export interface DeleteImageAssetResponse {
  asset_id: string;
  deleted: boolean;
  deleted_at: string;
}

export interface UploadImageOptions {
  usage_type: string;
  owner_type?: string;
  owner_id?: string;
  visibility?: "private" | "internal" | "public";
  caption?: string;
  wechat_code?: string;
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

export function buildUserAvatarContentUrl(assetId: string): string {
  return buildFileAssetContentUrl(assetId, "avatar_profile");
}

const LEGACY_USER_AVATAR_ASSET_ID_PATTERN =
  /\/catmap\/[^/]+\/user\/[^/]+\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\//i;

export function resolveUserAvatarContentUrl(avatarUrl: string | null | undefined): string | null {
  if (!avatarUrl) {
    return null;
  }

  const assetId = avatarUrl.match(LEGACY_USER_AVATAR_ASSET_ID_PATTERN)?.[1];
  return assetId ? buildUserAvatarContentUrl(assetId) : avatarUrl;
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

function submitImageUpload(
  accessToken: string,
  filePath: string,
  options: UploadImageOptions,
): Promise<UploadedImageAsset> {
  const wechatCodePromise = options.usage_type === "user_avatar"
    ? requestWechatLoginCode()
    : Promise.resolve(null);
  return wechatCodePromise.then(
    (wechatCode) =>
      new Promise((resolve, reject) => {
        uni.uploadFile({
          url: buildRequestUrl(appEnv.apiBaseUrl, API_ENDPOINTS.files.images),
          filePath,
          name: "file",
          header: createAuthorizationHeader(accessToken),
          formData: compactFormData({
            ...options,
            ...(wechatCode ? { wechat_code: wechatCode } : {}),
          }),
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
      }),
  );
}

export async function uploadImage(
  accessToken: string,
  filePath: string,
  options: UploadImageOptions,
): Promise<ApprovedImageAsset> {
  const asset = await submitImageUpload(accessToken, filePath, options);
  if (!asset.default_url) {
    throw new ApiBusinessError(65011, "图片处理失败，请重新上传", "", asset);
  }
  return asset as ApprovedImageAsset;
}

export function uploadUserAvatar(
  accessToken: string,
  filePath: string,
  ownerId?: string,
): Promise<UploadedImageAsset> {
  return submitImageUpload(accessToken, filePath, {
    usage_type: "user_avatar",
    owner_type: "user",
    owner_id: ownerId,
    visibility: "public",
    caption: "用户头像",
  });
}

export function deleteImageAsset(
  accessToken: string,
  assetId: string,
): Promise<DeleteImageAssetResponse> {
  return request<DeleteImageAssetResponse>({
    url: API_ENDPOINTS.files.asset(assetId),
    method: "DELETE",
    token: accessToken,
  });
}
