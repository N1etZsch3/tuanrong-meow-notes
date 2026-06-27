import { request } from "@/services/request";

export interface CatStatsResponse {
  total_cats: number;
  active_cats: number;
  waiting_adoption_cats: number;
  watching_cats: number;
  neutered_cats: number;
  neuter_rate: number;
}

export interface CatFilterOptionValue {
  value: string;
  label: string;
}

export interface CatFilterOption {
  key: string;
  label: string;
  values: CatFilterOptionValue[];
}

export interface CatSortOption {
  value: string;
  label: string;
}

export interface CatFilterOptionsResponse {
  filter_options: CatFilterOption[];
  sort_options: CatSortOption[];
}

export interface CatListItemDto {
  cat_id: string;
  name: string;
  avatar_url: string | null;
  avatar_thumbnail_url: string | null;
  coat_color: string;
  alias_summary: string | null;
  sex: string;
  neuter_status: string;
  health_status: string;
  status: string;
  personality_tags: string[];
  resident_area_text: string;
  last_seen_at: string | null;
  display_tags: string[];
  is_favorited: boolean;
}

export interface CatListResponse {
  items: CatListItemDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface CatListQuery {
  keyword?: string;
  filter_key?: string;
  filter_value?: string;
  sort?: string;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
}

function compactQuery<T extends object>(query: T): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(query as Record<string, unknown>).filter(
      ([, value]) => value !== undefined && value !== null && value !== "",
    ),
  );
}

export function getCatStats(accessToken: string): Promise<CatStatsResponse> {
  return request<CatStatsResponse>({
    url: "/cats/stats",
    method: "GET",
    token: accessToken,
  });
}

export function getCatFilterOptions(
  accessToken: string,
): Promise<CatFilterOptionsResponse> {
  return request<CatFilterOptionsResponse>({
    url: "/cats/filter-options",
    method: "GET",
    token: accessToken,
  });
}

export function getCats(
  accessToken: string,
  query: CatListQuery = {},
): Promise<CatListResponse> {
  return request<CatListResponse>({
    url: "/cats",
    method: "GET",
    data: compactQuery(query),
    token: accessToken,
  });
}
