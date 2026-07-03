import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";

export interface LngLatDto {
  lng: number;
  lat: number;
}

export interface LngLatBoundsDto {
  south_west: LngLatDto;
  north_east: LngLatDto;
}

export interface CampusDto {
  campus_id: string;
  name: string;
  center_lng: number;
  center_lat: number;
  default_zoom: number;
  min_zoom: number | null;
  max_zoom: number | null;
  boundary: unknown | null;
  core_bounds?: LngLatBoundsDto | null;
  limit_bounds?: LngLatBoundsDto | null;
}

export interface CampusAreaDto {
  area_id: string;
  parent_id: string | null;
  name: string;
  area_type: string;
  center_lng: number | null;
  center_lat: number | null;
  sort_order: number;
}

export interface MarkerConfigDto {
  marker_key: string;
  point_type: string;
  business_type: string | null;
  label: string;
  icon_url: string | null;
  icon_svg: string | null;
  color: string | null;
  z_index: number;
  default_visible: boolean;
  default_label_min_zoom: number;
  default_preview_min_zoom: number;
  default_preview_enabled: boolean;
  icon_width: number | null;
  icon_height: number | null;
  anchor_x: number | null;
  anchor_y: number | null;
}

export interface AmapConfigDto {
  web_key: string;
  security_js_code: string;
  map_style: string;
}

export interface TencentMapConfigDto {
  map_provider: "tencent";
  referer: string;
}

export interface TencentPoiDto {
  provider: "tencent";
  poi_id: string | null;
  name: string;
  address: string | null;
  category: string | null;
  lng: number;
  lat: number;
  distance_meters: number | null;
  match_method: string | null;
}

export interface MapFilterOptionDto {
  key: string;
  label: string;
  description?: string | null;
  icon_key?: string | null;
  point_types?: string[];
  business_types?: string[];
}

export interface MapInitResponse {
  campus: CampusDto;
  areas: CampusAreaDto[];
  marker_configs: MarkerConfigDto[];
  filter_options?: MapFilterOptionDto[];
  default_filters: {
    point_types?: string[];
    include_hidden?: boolean;
    only_available_tasks?: boolean;
  };
  ui_config: {
    show_title?: boolean;
    search_placeholder?: string;
    bottom_default_mode?: string;
  };
  tencent_config?: TencentMapConfigDto;
  amap_config?: AmapConfigDto;
}

export interface MapPointMarkerDto {
  point_id: string;
  point_type: string;
  point_scope: string;
  business_type: string | null;
  business_id: string | null;
  name: string;
  subtitle: string | null;
  lng: number;
  lat: number;
  area_id: string | null;
  area_name: string | null;
  marker_key: string | null;
  icon_key: string | null;
  display_level: number;
  visibility: string;
  status: string;
  cover_photo_url: string | null;
  preview_enabled: boolean;
  preview_min_zoom: number;
  label_min_zoom: number;
  distance_meters: number | null;
  extra: Record<string, unknown>;
}

export interface MapPointsResponse {
  items: MapPointMarkerDto[];
  total: number;
  map_strategy?: {
    cluster_enabled?: boolean;
    label_collision?: string;
    max_marker_count?: number;
  };
}

export interface MapSearchResultDto {
  result_type: string;
  map_point_id: string | null;
  business_id: string | null;
  point_type: string;
  business_type: string | null;
  title: string;
  subtitle: string | null;
  description: string | null;
  icon_key: string | null;
  cover_photo_url: string | null;
  lng: number;
  lat: number;
  distance_meters: number | null;
  status_label: string | null;
  highlight_text: string | null;
  sort_score: number;
  poi?: TencentPoiDto | null;
}

export interface MapSearchResponse {
  items: MapSearchResultDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
  suggestions: string[];
}

export interface MapTaskActiveExecutionDto {
  execution_date_id: string;
  execute_date: string;
  status?: string | null;
  display_status?: string | null;
  display_status_label?: string | null;
}

export interface MapBottomContentItemDto {
  id: string;
  map_point_id?: string;
  type: string;
  title: string;
  subtitle: string | null;
  description: string | null;
  distance_meters: number | null;
  status_label: string | null;
  tag_label: string | null;
  cover_photo_url: string | null;
  lng?: number | null;
  lat?: number | null;
  active_execution?: MapTaskActiveExecutionDto | null;
}

export interface MapBottomContentResponse {
  content_type: string;
  title: string;
  items: MapBottomContentItemDto[];
}

export interface MapPointPhotoDto {
  photo_id: string;
  photo_type: string;
  file_url: string;
  thumbnail_url: string | null;
  caption: string | null;
  sort_order: number;
  created_at: string;
}

export interface CardActionDto {
  key: string;
  label: string;
  enabled: boolean;
  disabled_reason: string | null;
  method: string | null;
  path: string | null;
  target_type: string;
}

export interface MapPointSummaryResponse {
  point_id: string;
  point_type: string;
  business_type: string | null;
  business_id: string | null;
  title: string;
  subtitle: string | null;
  cover_photo_url: string | null;
  tags: string[];
  description: string | null;
  location_name: string | null;
  location_detail: string | null;
  route_instruction: string | null;
  landmark_hint: string | null;
  entrance_hint: string | null;
  lng: number;
  lat: number;
  distance_meters: number | null;
  associated_poi?: TencentPoiDto | null;
  photos: MapPointPhotoDto[];
  business_summary: Record<string, unknown>;
  actions: CardActionDto[];
}

export interface MapNavigationResponse {
  point_id: string;
  title: string;
  destination: {
    lng: number;
    lat: number;
    location_name: string;
    amap_poi_id: string | null;
    amap_address: string | null;
    associated_poi?: TencentPoiDto | null;
  };
  route_instruction: string | null;
  landmark_hint: string | null;
  entrance_hint: string | null;
  photos: MapPointPhotoDto[];
  amap_navigation: {
    mode: string;
    open_url: string;
    web_url: string;
  };
  tencent_navigation?: {
    mode: string;
    web_url: string;
  };
  route: {
    provider: string;
    fallback: boolean;
    distance_meters: number | null;
    duration_seconds: number | null;
    points: Array<{ lng: number; lat: number }>;
    steps: Array<{
      instruction: string;
      distance_meters: number;
      duration_seconds: number;
      points: Array<{ lng: number; lat: number }>;
    }>;
  };
}

export interface MapPointQuery {
  campus_id?: string;
  filter_key?: string;
  point_types?: string;
  business_types?: string;
  area_id?: string;
  min_lng?: number;
  min_lat?: number;
  max_lng?: number;
  max_lat?: number;
  user_lng?: number;
  user_lat?: number;
}

export interface MapSearchQuery {
  keyword: string;
  campus_id?: string;
  point_types?: string;
  include_external?: boolean;
  user_lng?: number;
  user_lat?: number;
  page?: number;
  page_size?: number;
}

export interface MapBottomContentQuery {
  mode?: string;
  limit?: number;
}

export interface MapNavigationQuery {
  from_lng?: number;
  from_lat?: number;
  mode?: "walking";
}

export interface MapPoiResolveQuery {
  keyword?: string;
  lng: number;
  lat: number;
  radius?: number;
  limit?: number;
}

export interface MapPoiNearbyQuery {
  lng: number;
  lat: number;
  keyword?: string;
  radius?: number;
  limit?: number;
}

export interface MapPoiResolveResponse {
  query: Record<string, unknown>;
  matched_poi: TencentPoiDto;
  candidates: TencentPoiDto[];
}

export interface MapPoiNearbyResponse {
  query: Record<string, unknown>;
  recommended: TencentPoiDto | null;
  candidates: TencentPoiDto[];
}

export interface WalkingRouteQuery {
  from_lng: number;
  from_lat: number;
  to_lng: number;
  to_lat: number;
}

export type WalkingRouteResponse = MapNavigationResponse["route"];

export function getMapInit(accessToken: string): Promise<MapInitResponse> {
  return request<MapInitResponse>({
    url: API_ENDPOINTS.map.init,
    method: "GET",
    token: accessToken,
  });
}

export function getMapPoints(
  accessToken: string,
  query: MapPointQuery = {},
): Promise<MapPointsResponse> {
  return request<MapPointsResponse>({
    url: API_ENDPOINTS.map.points,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function searchMap(
  accessToken: string,
  query: MapSearchQuery,
): Promise<MapSearchResponse> {
  return request<MapSearchResponse>({
    url: API_ENDPOINTS.map.search,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getMapBottomContent(
  accessToken: string,
  query: MapBottomContentQuery = {},
): Promise<MapBottomContentResponse> {
  return request<MapBottomContentResponse>({
    url: API_ENDPOINTS.map.bottomContent,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getMapPointSummary(
  accessToken: string,
  pointId: string,
  query: Pick<MapPointQuery, "user_lng" | "user_lat"> = {},
): Promise<MapPointSummaryResponse> {
  return request<MapPointSummaryResponse>({
    url: API_ENDPOINTS.map.pointSummary(pointId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getMapPointNavigation(
  accessToken: string,
  pointId: string,
  query: MapNavigationQuery = {},
): Promise<MapNavigationResponse> {
  return request<MapNavigationResponse>({
    url: API_ENDPOINTS.map.pointNavigation(pointId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function resolveMapPoi(
  accessToken: string,
  query: MapPoiResolveQuery,
): Promise<MapPoiResolveResponse> {
  return request<MapPoiResolveResponse>({
    url: API_ENDPOINTS.map.poiResolve,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getNearbyMapPois(
  accessToken: string,
  query: MapPoiNearbyQuery,
): Promise<MapPoiNearbyResponse> {
  return request<MapPoiNearbyResponse>({
    url: API_ENDPOINTS.map.poiNearby,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getWalkingRoute(
  accessToken: string,
  query: WalkingRouteQuery,
): Promise<WalkingRouteResponse> {
  return request<WalkingRouteResponse>({
    url: API_ENDPOINTS.map.walkingRoute,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}
