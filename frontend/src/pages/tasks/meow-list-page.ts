import type { MapPointMarkerDto } from "@/api/map";

export interface MeowPointListItem {
  point_id: string;
  detail_id: string;
  title: string;
  nearby_landmark_name: string;
  cover_photo_url: string | null;
  subtitle: string | null;
  area_name: string | null;
}

export interface MeowPointListResponse {
  items: MeowPointListItem[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

interface AssociatedPoiLike {
  name?: unknown;
  address?: unknown;
}

function trimText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function readAssociatedPoi(extra: Record<string, unknown>): AssociatedPoiLike | null {
  const associatedPoi = extra.associated_poi;
  if (!associatedPoi || typeof associatedPoi !== "object") {
    return null;
  }

  return associatedPoi as AssociatedPoiLike;
}

export function getMarkerNearbyLandmarkName(marker: MapPointMarkerDto): string {
  const associatedPoi = readAssociatedPoi(marker.extra);
  const poiName = trimText(associatedPoi?.name);
  if (poiName) {
    return poiName;
  }

  const poiAddress = trimText(associatedPoi?.address);
  if (poiAddress) {
    return poiAddress;
  }

  const locationDetail = trimText(marker.extra.location_detail);
  if (locationDetail) {
    return locationDetail;
  }

  return marker.area_name || marker.subtitle || "暂无附近地标";
}

export function mapMarkerToMeowPointListItem(
  marker: MapPointMarkerDto,
): MeowPointListItem {
  return {
    point_id: marker.point_id,
    detail_id: marker.business_id || marker.point_id,
    title: marker.name || marker.subtitle || "未命名点位",
    nearby_landmark_name: getMarkerNearbyLandmarkName(marker),
    cover_photo_url: marker.cover_photo_url,
    subtitle: marker.subtitle,
    area_name: marker.area_name,
  };
}

export function mapMarkersToMeowPointListItems(
  markers: MapPointMarkerDto[],
): MeowPointListItem[] {
  return markers.map(mapMarkerToMeowPointListItem);
}

export function filterPointListByKeyword(
  items: MeowPointListItem[],
  keyword: string,
): MeowPointListItem[] {
  const normalizedKeyword = keyword.trim().toLowerCase();
  if (!normalizedKeyword) {
    return items;
  }

  return items.filter((item) => {
    const searchableText = [
      item.title,
      item.nearby_landmark_name,
      item.subtitle,
      item.area_name,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return searchableText.includes(normalizedKeyword);
  });
}
