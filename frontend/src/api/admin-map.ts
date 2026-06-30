import { request } from "@/services/request";
import type { TencentPoiDto } from "@/api/map";

export interface AdminMapPointPhotoDto {
  photo_id: string;
  photo_type: string;
  file_url: string;
  thumbnail_url: string | null;
  caption: string | null;
  sort_order: number;
  created_at: string;
}

export interface AdminMapPointDto {
  point_id: string;
  campus_id: string;
  area_id: string | null;
  point_type: string;
  point_scope: string;
  name: string;
  subtitle: string | null;
  description: string | null;
  location_name: string | null;
  location_detail: string | null;
  lng: number;
  lat: number;
  amap_poi_id: string | null;
  amap_address: string | null;
  tencent_poi_id: string | null;
  tencent_poi_name: string | null;
  tencent_poi_address: string | null;
  tencent_poi_category: string | null;
  tencent_poi_lng: number | null;
  tencent_poi_lat: number | null;
  tencent_poi_distance_meters: number | null;
  tencent_poi_match_method: string | null;
  associated_poi: TencentPoiDto | null;
  route_instruction: string | null;
  landmark_hint: string | null;
  entrance_hint: string | null;
  icon_key: string | null;
  display_level: number;
  label_min_zoom: number;
  preview_enabled: boolean;
  preview_min_zoom: number;
  visibility: string;
  status: string;
  cover_photo_url: string | null;
  photos: AdminMapPointPhotoDto[];
  updated_at: string;
}

export interface AdminMapPointUpdatePayload {
  area_id?: string | null;
  point_type?: string;
  point_scope?: string;
  name?: string;
  subtitle?: string | null;
  description?: string | null;
  location_name?: string | null;
  location_detail?: string | null;
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
  route_instruction?: string | null;
  landmark_hint?: string | null;
  entrance_hint?: string | null;
  icon_key?: string | null;
  display_level?: number;
  label_min_zoom?: number;
  preview_enabled?: boolean;
  preview_min_zoom?: number;
  visibility?: string;
  status?: string;
}

export interface AdminMapPointLocationPayload {
  lng: number;
  lat: number;
}

function compactPayload<T extends object>(payload: T): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(payload as Record<string, unknown>).filter(
      ([, value]) => value !== undefined,
    ),
  );
}

export function getAdminMapPoint(
  accessToken: string,
  pointId: string,
): Promise<AdminMapPointDto> {
  return request<AdminMapPointDto>({
    url: `/admin/map/points/${pointId}`,
    method: "GET",
    token: accessToken,
  });
}

export function updateAdminMapPoint(
  accessToken: string,
  pointId: string,
  payload: AdminMapPointUpdatePayload,
): Promise<AdminMapPointDto> {
  return request<AdminMapPointDto>({
    url: `/admin/map/points/${pointId}`,
    method: "PATCH",
    data: compactPayload(payload),
    token: accessToken,
  });
}

export function updateAdminMapPointLocation(
  accessToken: string,
  pointId: string,
  payload: AdminMapPointLocationPayload,
): Promise<AdminMapPointDto> {
  return request<AdminMapPointDto>({
    url: `/admin/map/points/${pointId}/location`,
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}
