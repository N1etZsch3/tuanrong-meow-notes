import type {
  LandmarkCreatePayload,
  LandmarkDetailDto,
  LandmarkPhotoDto,
  LandmarkPhotoPayload,
} from "@/api/landmarks";
import type { TencentPoiDto } from "@/api/map";
import type { ApprovedImageAsset } from "@/api/files";

export const LANDMARK_LOCATION_STORAGE_KEY = "catmap_admin_landmark_location";

export interface SelectedLandmarkLocation {
  campus_id?: string;
  area_id?: string | null;
  location_name: string;
  location_detail: string;
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
}

export interface LandmarkDraft {
  name: string;
  description: string;
  location: SelectedLandmarkLocation | null;
  photos: LandmarkPhotoPayload[];
}

export const HBNU_DEFAULT_LANDMARK_LOCATION: SelectedLandmarkLocation = {
  location_name: "",
  location_detail: "",
  lng: 115.062202,
  lat: 30.22991,
  route_instruction: "",
  landmark_hint: "",
  entrance_hint: "",
  amap_poi_id: null,
  amap_address: null,
  tencent_poi_id: null,
  tencent_poi_name: null,
  tencent_poi_address: null,
  tencent_poi_category: null,
  tencent_poi_lng: null,
  tencent_poi_lat: null,
  tencent_poi_distance_meters: null,
  tencent_poi_match_method: null,
};

export function createDefaultLandmarkDraft(): LandmarkDraft {
  return {
    name: "",
    description: "",
    location: null,
    photos: [],
  };
}

export function buildUploadedLandmarkPhoto(asset: ApprovedImageAsset): LandmarkPhotoPayload {
  return {
    file_id: asset.asset_id,
    file_url: asset.default_url,
    thumbnail_url: asset.default_thumb_url,
    photo_type: "scene",
    caption: "地标照片",
    sort_order: 0,
  };
}

export function landmarkPhotoToUploadedRef(photo: LandmarkPhotoDto): LandmarkPhotoPayload {
  return {
    file_url: photo.file_url,
    thumbnail_url: photo.thumbnail_url,
    photo_type: photo.photo_type,
    caption: photo.caption,
    sort_order: photo.sort_order,
    is_cover: photo.photo_type === "cover",
  };
}

export function getLandmarkPhotoDisplayUrl(photo: LandmarkPhotoDto | LandmarkPhotoPayload): string {
  return photo.thumbnail_url || photo.file_url;
}

export function selectedLocationAssociatedPoi(
  location: SelectedLandmarkLocation,
): TencentPoiDto | null {
  if (!location.tencent_poi_id && !location.tencent_poi_name) {
    return null;
  }
  return {
    provider: "tencent",
    poi_id: location.tencent_poi_id || null,
    name: location.tencent_poi_name || "",
    address: location.tencent_poi_address || null,
    category: location.tencent_poi_category || null,
    lng: location.tencent_poi_lng || location.lng,
    lat: location.tencent_poi_lat || location.lat,
    distance_meters: location.tencent_poi_distance_meters ?? null,
    match_method: location.tencent_poi_match_method || "admin_selected",
  };
}

export function validateLandmarkDraft(draft: LandmarkDraft): { valid: boolean; message?: string } {
  if (!draft.name.trim()) {
    return { valid: false, message: "请填写地标名称" };
  }
  if (!draft.location) {
    return { valid: false, message: "请选择地标位置" };
  }
  if (!draft.location.location_detail.trim()) {
    return { valid: false, message: "请填写地标位置说明" };
  }
  if (!draft.description.trim()) {
    return { valid: false, message: "请填写地标说明" };
  }
  return { valid: true };
}

export function buildLandmarkPayload(draft: LandmarkDraft): LandmarkCreatePayload {
  const location = draft.location || {
    ...HBNU_DEFAULT_LANDMARK_LOCATION,
    location_name: draft.name.trim(),
  };
  const description = draft.description.trim();
  return {
    name: draft.name.trim(),
    description,
    map_point: {
      ...location,
      location_name: draft.name.trim(),
      route_instruction: description,
    },
    photos: draft.photos.map((photo, index) => ({
      ...photo,
      photo_type: index === 0 ? "cover" : "scene",
      sort_order: index,
      is_cover: index === 0,
    })),
    is_public: true,
  };
}

export function detailToDraft(detail: LandmarkDetailDto): LandmarkDraft {
  return {
    name: detail.name || "",
    description: detail.description || detail.map_point.route_instruction || "",
    location: {
      campus_id: detail.map_point.campus_id,
      area_id: detail.map_point.area_id,
      location_name: detail.name,
      location_detail: detail.map_point.location_detail || "",
      lng: detail.map_point.lng,
      lat: detail.map_point.lat,
      route_instruction: detail.map_point.route_instruction,
      landmark_hint: detail.map_point.landmark_hint,
      entrance_hint: detail.map_point.entrance_hint,
      amap_poi_id: detail.map_point.amap_poi_id,
      amap_address: detail.map_point.amap_address,
      tencent_poi_id: detail.map_point.tencent_poi_id,
      tencent_poi_name: detail.map_point.tencent_poi_name,
      tencent_poi_address: detail.map_point.tencent_poi_address,
      tencent_poi_category: detail.map_point.tencent_poi_category,
      tencent_poi_lng: detail.map_point.tencent_poi_lng,
      tencent_poi_lat: detail.map_point.tencent_poi_lat,
      tencent_poi_distance_meters: detail.map_point.tencent_poi_distance_meters,
      tencent_poi_match_method: detail.map_point.tencent_poi_match_method,
    },
    photos: detail.photos.map(landmarkPhotoToUploadedRef),
  };
}
