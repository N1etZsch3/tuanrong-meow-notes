import { request } from "@/services/request";
import { API_ENDPOINTS } from "@/api/routes";
import type { TencentPoiDto } from "@/api/map";
import type { UploadedFileRef } from "@/api/supplies";

export interface LandmarkMapPointPayload {
  campus_id?: string;
  area_id?: string | null;
  location_name?: string;
  location_detail?: string | null;
  lng?: number;
  lat?: number;
  route_instruction?: string | null;
  landmark_hint?: string | null;
  entrance_hint?: string | null;
  amap_poi_id?: string | null;
  amap_address?: string | null;
  tencent_poi_id?: string | null;
  tencent_poi_name?: string | null;
  tencent_poi_address?: string | null;
  tencent_poi_category?: string | null;
  tencent_poi_lng?: number | null;
  tencent_poi_lat?: number | null;
  tencent_poi_distance_meters?: number | null;
  tencent_poi_match_method?: string | null;
  associated_poi?: TencentPoiDto | null;
}

export interface LandmarkPhotoPayload extends UploadedFileRef {
  photo_type?: string;
  caption?: string | null;
  sort_order?: number;
  is_cover?: boolean;
}

export interface LandmarkCreatePayload {
  name: string;
  description?: string | null;
  map_point: LandmarkMapPointPayload;
  photos?: LandmarkPhotoPayload[];
  is_public?: boolean;
}

export interface LandmarkCreateResponse {
  landmark_id: string;
  map_point_id: string;
  status: string;
  photo_count: number;
  created_at: string;
}

export interface LandmarkDeleteResponse {
  landmark_id: string;
  deleted_at: string;
}

export interface LandmarkPhotoDto {
  photo_id: string;
  photo_type: string;
  file_url: string;
  thumbnail_url: string | null;
  caption: string | null;
  sort_order: number;
  created_at: string;
}

export interface LandmarkDetailDto {
  landmark_id: string;
  map_point_id: string;
  name: string;
  description: string | null;
  status: string;
  is_public: boolean;
  map_point: LandmarkMapPointPayload & {
    map_point_id: string;
    point_type: string;
    point_scope: string;
    name: string;
    location_name: string | null;
    lng: number;
    lat: number;
  };
  photos: LandmarkPhotoDto[];
  created_at: string;
  updated_at: string;
}

export function createLandmark(
  accessToken: string,
  payload: LandmarkCreatePayload,
): Promise<LandmarkCreateResponse> {
  return request<LandmarkCreateResponse, LandmarkCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.landmarkPoints,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateLandmark(
  accessToken: string,
  landmarkId: string,
  payload: LandmarkCreatePayload,
): Promise<LandmarkDetailDto> {
  return request<LandmarkDetailDto, LandmarkCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.landmarkPoint(landmarkId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function deleteLandmark(
  accessToken: string,
  landmarkId: string,
): Promise<LandmarkDeleteResponse> {
  return request<LandmarkDeleteResponse>({
    url: API_ENDPOINTS.admin.landmarkPoint(landmarkId),
    method: "DELETE",
    token: accessToken,
  });
}

export function getAdminLandmarkDetail(
  accessToken: string,
  landmarkId: string,
): Promise<LandmarkDetailDto> {
  return request<LandmarkDetailDto>({
    url: API_ENDPOINTS.admin.landmarkPoint(landmarkId),
    method: "GET",
    token: accessToken,
  });
}

export function getLandmarkDetail(
  accessToken: string,
  landmarkId: string,
): Promise<LandmarkDetailDto> {
  return request<LandmarkDetailDto>({
    url: API_ENDPOINTS.landmarks.detail(landmarkId),
    method: "GET",
    token: accessToken,
  });
}
