import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";
import type { TencentPoiDto } from "@/api/map";
import type { MeowPointListResponse } from "@/pages/tasks/meow-list-page";

export interface MeowPointListQuery {
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface UploadedFileRef {
  file_id?: string | null;
  file_url: string;
  thumbnail_url?: string | null;
  cos_object_key?: string | null;
}

export interface SupplyMapPointPayload {
  campus_id?: string;
  area_id?: string | null;
  location_name: string;
  location_detail?: string | null;
  lng: number;
  lat: number;
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

export interface SupplyItemPayload {
  item_name: string;
  item_type: string;
  quantity: number;
  unit?: string | null;
  icon_key?: string | null;
  color_key?: string | null;
  is_custom?: boolean;
  sort_order?: number;
}

export interface SupplyPhotoPayload extends UploadedFileRef {
  photo_type?: string;
  caption?: string | null;
  sort_order?: number;
  is_cover?: boolean;
}

export interface SupplyPointCreatePayload {
  name: string;
  description?: string | null;
  usage_instruction?: string | null;
  access_instruction?: string | null;
  map_point_id?: string;
  map_point?: SupplyMapPointPayload;
  items: SupplyItemPayload[];
  photos?: SupplyPhotoPayload[];
  is_public?: boolean;
}

export interface SupplyPointCreateResponse {
  supply_point_id: string;
  map_point_id: string;
  status: string;
  initial_item_count: number;
  photo_count: number;
  created_at: string;
}

export interface SupplyPointUpdateResponse {
  supply_point_id: string;
  updated_at: string;
}

export interface SupplyPointDeleteResponse {
  supply_point_id: string;
  deleted_at: string;
}

export interface SupplyUserDto {
  user_id: string;
  nickname: string;
  avatar_url: string | null;
}

export interface SupplyItemDto {
  item_id: string | null;
  source_item_id?: string | null;
  item_name: string;
  item_type: string;
  quantity: number;
  unit: string | null;
  icon_key: string | null;
  color_key: string | null;
  is_custom: boolean;
  sort_order: number;
  label: string;
}

export interface SupplyPhotoDto {
  photo_id: string;
  photo_type: string;
  file_url: string;
  thumbnail_url: string | null;
  caption: string | null;
  sort_order: number;
  created_at: string;
}

export interface SupplyRecordDto {
  record_id: string;
  supply_point_id: string;
  recorded_at: string;
  match_status: "matched" | "mismatch" | string;
  display_tone: "success" | "danger" | string;
  recorder: SupplyUserDto | null;
  photo: UploadedFileRef;
  remark: string | null;
  items: SupplyItemDto[];
}

export interface SupplyRecordsResponse {
  items: SupplyRecordDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface SupplyPointDetailDto {
  supply_point_id: string;
  map_point_id: string;
  name: string;
  description: string | null;
  usage_instruction: string | null;
  access_instruction: string | null;
  status: string;
  is_public: boolean;
  map_point: SupplyMapPointPayload & {
    map_point_id: string;
    point_type: string;
    point_scope: string;
  };
  photos: SupplyPhotoDto[];
  initial_items: SupplyItemDto[];
  current_state_source: "initial" | "latest_record" | string;
  current_items: SupplyItemDto[];
  latest_record: SupplyRecordDto | null;
  records: SupplyRecordsResponse;
  created_at: string;
  updated_at: string;
}

export interface SupplyRecordCreatePayload {
  items: Array<{
    item_id: string;
    quantity: number;
  }>;
  photo: UploadedFileRef;
  remark?: string | null;
}

export interface SupplyRecordQuery {
  record_date?: string;
  record_week_start?: string;
  record_month?: string;
  record_page?: number;
  record_page_size?: number;
  page?: number;
  page_size?: number;
}

export function createSupplyPoint(
  payload: SupplyPointCreatePayload,
  accessToken: string,
): Promise<SupplyPointCreateResponse> {
  return request<SupplyPointCreateResponse, SupplyPointCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.supplyPoints,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateSupplyPoint(
  accessToken: string,
  supplyPointId: string,
  payload: SupplyPointCreatePayload,
): Promise<SupplyPointUpdateResponse> {
  return request<SupplyPointUpdateResponse, SupplyPointCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.supplyPoint(supplyPointId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function deleteSupplyPoint(
  accessToken: string,
  supplyPointId: string,
): Promise<SupplyPointDeleteResponse> {
  return request<SupplyPointDeleteResponse>({
    url: API_ENDPOINTS.admin.supplyPoint(supplyPointId),
    method: "DELETE",
    token: accessToken,
  });
}

export function getAdminSupplyPointDetail(
  accessToken: string,
  supplyPointId: string,
): Promise<SupplyPointDetailDto> {
  return request<SupplyPointDetailDto>({
    url: API_ENDPOINTS.admin.supplyPoint(supplyPointId),
    method: "GET",
    token: accessToken,
  });
}

export function getSupplyPointDetail(
  accessToken: string,
  supplyPointId: string,
  query: SupplyRecordQuery = {},
): Promise<SupplyPointDetailDto> {
  return request<SupplyPointDetailDto>({
    url: API_ENDPOINTS.supplies.detail(supplyPointId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getSupplyRecords(
  accessToken: string,
  supplyPointId: string,
  query: SupplyRecordQuery = {},
): Promise<SupplyRecordsResponse> {
  return request<SupplyRecordsResponse>({
    url: API_ENDPOINTS.supplies.records(supplyPointId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function createSupplyRecord(
  accessToken: string,
  supplyPointId: string,
  payload: SupplyRecordCreatePayload,
): Promise<SupplyRecordDto> {
  return request<SupplyRecordDto, SupplyRecordCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.supplies.records(supplyPointId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function getSupplyPoints(
  accessToken: string,
  query: MeowPointListQuery = {},
): Promise<MeowPointListResponse> {
  return request<MeowPointListResponse>({
    url: API_ENDPOINTS.supplies.list,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}
