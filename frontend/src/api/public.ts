import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";

export interface PublicStats {
  in_campus_cats: number;
  neuter_rate: number;
  adopted_cats: number;
  watching_cats: number;
  total_cats: number;
}

export interface PublicSiteIntroSection {
  title: string;
  text: string;
}

export interface PublicSiteInfo {
  name: string;
  association_name: string;
  university?: string;
  slogan: string;
  intro_paragraphs: string[];
  intro_sections?: PublicSiteIntroSection[];
  highlight_note?: string;
  join_info: string;
  contact_info: string;
  feeding_tips: string[];
}

export interface PublicCatListItem {
  cat_id: string;
  name: string;
  avatar_url: string | null;
  coat_color: string;
  sex: string;
  neuter_status: string;
  status: string;
  personality_tags: string[];
  alias_summary: string | null;
}

export interface PublicCatPhoto {
  file_url: string;
  caption: string | null;
}

export interface PublicCatDetail {
  cat_id: string;
  name: string;
  aliases: string[];
  avatar_url: string | null;
  photos: PublicCatPhoto[];
  coat_color: string;
  sex: string;
  neuter_status: string;
  status: string;
  personality_tags: string[];
  story: string | null;
}

export interface PublicCatList {
  items: PublicCatListItem[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface PublicCatQuery {
  keyword?: string;
  coat_color?: string;
  sex?: string;
  status?: string;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
}

export type PublicPostType = "trivia" | "merch";

export interface PublicPostCard {
  post_id: string;
  post_type: PublicPostType;
  title: string;
  summary: string | null;
  cover_url: string | null;
  published_at: string | null;
}

export interface PublicPostBlock {
  block_type: string;
  text: string | null;
  image_url: string | null;
}

export interface PublicPostDetail {
  post_id: string;
  post_type: PublicPostType;
  title: string;
  summary: string | null;
  cover_url: string | null;
  published_at: string | null;
  blocks: PublicPostBlock[];
}

export interface PublicPostList {
  items: PublicPostCard[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface PublicPostQuery {
  type?: PublicPostType;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
}

export function getPublicStats(): Promise<PublicStats> {
  return request<PublicStats>({
    url: API_ENDPOINTS.public.stats,
    method: "GET",
  });
}

export function getPublicSiteInfo(): Promise<PublicSiteInfo> {
  return request<PublicSiteInfo>({
    url: API_ENDPOINTS.public.site,
    method: "GET",
  });
}

export function getPublicCats(query: PublicCatQuery = {}): Promise<PublicCatList> {
  return request<PublicCatList>({
    url: API_ENDPOINTS.public.cats,
    method: "GET",
    data: compactApiParams(query),
  });
}

export function getPublicCatDetail(catId: string): Promise<PublicCatDetail> {
  return request<PublicCatDetail>({
    url: API_ENDPOINTS.public.cat(catId),
    method: "GET",
  });
}

export function getPublicPosts(query: PublicPostQuery = {}): Promise<PublicPostList> {
  return request<PublicPostList>({
    url: API_ENDPOINTS.public.posts,
    method: "GET",
    data: compactApiParams(query),
  });
}

export function getPublicPostDetail(postId: string): Promise<PublicPostDetail> {
  return request<PublicPostDetail>({
    url: API_ENDPOINTS.public.post(postId),
    method: "GET",
  });
}
