import { request } from "@/services/request";
import type { UserRole } from "@/types/user";

export interface MeDashboardProfile {
  user_id: string;
  student_no: string;
  meow_no: string;
  nickname: string;
  avatar_url: string | null;
  department: string | null;
  role: UserRole;
  show_admin_entry: boolean;
}

export interface MeDashboardStats {
  total_completed_tasks: number;
  monthly_completed_tasks: number;
  current_in_progress_tasks: number;
  total_observation_records: number;
  favorite_cats: number;
}

export interface MeDashboardTodo {
  unread_notifications: number;
  pending_assignments: number;
  today_duty_count: number;
  in_progress_task_count: number;
}

export interface MeDashboardResponse {
  profile: MeDashboardProfile;
  stats: MeDashboardStats;
  todo: MeDashboardTodo;
  recent_tasks: Array<Record<string, unknown>>;
  recent_notifications: Array<Record<string, unknown>>;
}

export interface EmptyRecordPage {
  items: Array<Record<string, unknown>>;
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

interface PageQuery {
  page?: number;
  page_size?: number;
}

function buildPageUrl(path: string, query: PageQuery = {}): string {
  const suffix = Object.entries({
    page: query.page ? String(query.page) : undefined,
    page_size: query.page_size ? String(query.page_size) : undefined,
  })
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value || "")}`)
    .join("&");
  return suffix ? `${path}?${suffix}` : path;
}

export function getMeDashboard(accessToken: string): Promise<MeDashboardResponse> {
  return request<MeDashboardResponse>({
    url: "/me/dashboard",
    method: "GET",
    token: accessToken,
  });
}

export function getMyTasks(
  accessToken: string,
  query?: PageQuery,
): Promise<EmptyRecordPage> {
  return request<EmptyRecordPage>({
    url: buildPageUrl("/me/tasks", query),
    method: "GET",
    token: accessToken,
  });
}

export function getMyCheckins(
  accessToken: string,
  query?: PageQuery,
): Promise<EmptyRecordPage> {
  return request<EmptyRecordPage>({
    url: buildPageUrl("/me/checkins", query),
    method: "GET",
    token: accessToken,
  });
}

export function getMyObservations(
  accessToken: string,
  query?: PageQuery,
): Promise<EmptyRecordPage> {
  return request<EmptyRecordPage>({
    url: buildPageUrl("/me/observations", query),
    method: "GET",
    token: accessToken,
  });
}

export function getFavoriteCats(
  accessToken: string,
  query?: PageQuery,
): Promise<EmptyRecordPage> {
  return request<EmptyRecordPage>({
    url: buildPageUrl("/me/favorite-cats", query),
    method: "GET",
    token: accessToken,
  });
}
