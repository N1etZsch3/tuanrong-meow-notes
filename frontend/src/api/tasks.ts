import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";
import type { TencentPoiDto } from "@/api/map";

export interface UploadedFileRef {
  file_id: string | null;
  file_url: string;
  thumbnail_url?: string | null;
  cos_object_key?: string | null;
}

export interface TaskPhotoPayload extends UploadedFileRef {
  photo_type?: string;
  caption?: string | null;
  sort_order?: number;
  is_cover?: boolean;
}

export interface TaskMapPointPayload {
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

export interface SummerFeedingTaskCreatePayload {
  title: string;
  description?: string | null;
  required_items?: string | null;
  execute_dates: string[];
  map_point_id?: string;
  map_point?: TaskMapPointPayload;
  photos?: TaskPhotoPayload[];
  is_public?: boolean;
}

export interface SummerFeedingTaskCreateResponse {
  task_id: string;
  task_no: string;
  map_point_id: string;
  task_type: string;
  task_mode: string;
  schedule_type: string;
  completion_policy: string;
  status: string;
  execution_date_count: number;
  photo_count: number;
  published_at: string;
}

export interface TaskExecutionDto {
  execution_date_id: string;
  execute_date: string;
  status: string;
  completed_by: {
    user_id: string;
    nickname: string;
    avatar_url: string | null;
  } | null;
  completed_at: string | null;
  checkin_id: string | null;
  remark: string | null;
}

export interface TaskListItemDto {
  task_id: string;
  title: string;
  task_type: string;
  status: string;
  status_label: string;
  description: string;
  required_items: string;
  cover_photo_url: string | null;
  map_point: {
    map_point_id: string;
    location_name: string;
    location_detail: string | null;
    lng: number;
    lat: number;
  };
  date_range: {
    start_date: string | null;
    end_date: string | null;
    total_count: number;
    completed_count: number;
    pending_count: number;
  };
  current_execution: TaskExecutionDto | null;
  next_execution: TaskExecutionDto | null;
  distance_meters: number | null;
  published_at: string;
}

export interface TaskListResponse {
  items: TaskListItemDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface TaskListQuery {
  task_type?: "feeding";
  status?: string;
  execution_status?: string;
  keyword?: string;
  execute_date?: string;
  execute_date_start?: string;
  execute_date_end?: string;
  only_today?: boolean;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
}

export interface TaskPhotoDto {
  photo_id: string;
  file_id: string | null;
  file_url: string;
  thumbnail_url: string | null;
  cos_object_key?: string | null;
  photo_type: string;
  caption: string | null;
  sort_order: number;
  is_cover: boolean;
  created_at: string;
}

export interface TaskActivityDto {
  activity_id: string;
  activity_type: string;
  title: string;
  content: string | null;
  execute_date: string | null;
  created_at: string;
}

export interface TaskDetailDto extends Omit<TaskListItemDto, "map_point"> {
  task_no: string;
  task_mode: string;
  schedule_type: string;
  completion_policy: string;
  map_point: TaskMapPointPayload & {
    map_point_id: string;
    point_type: string;
    point_scope: string;
  };
  photos: TaskPhotoDto[];
  execution_dates: TaskExecutionDto[];
  activities: TaskActivityDto[];
  actions: {
    can_navigate: boolean;
    can_checkin: boolean;
    checkin_disabled_reason: string | null;
    can_admin_edit: boolean;
  };
  created_at: string;
  updated_at: string;
}

export interface TaskCheckinPayload {
  execute_date?: string;
  is_completed?: boolean;
  process_result?: string | null;
  remark?: string | null;
  checkin_lng?: number;
  checkin_lat?: number;
  photos?: UploadedFileRef[];
}

export interface TaskCheckinResponse {
  execution_date_id: string;
  execute_date: string;
  status: string;
  checkin: {
    checkin_id: string;
    task_id: string;
    execute_date: string;
    is_completed: boolean;
    process_result: string | null;
    remark: string | null;
    submitted_at: string;
  };
}

export interface SummerFeedingTaskUpdateResponse {
  task_id: string;
  updated_at: string;
}

export interface TaskStatusUpdatePayload {
  status: "in_progress" | "completed" | "cancelled" | "archived";
  reason?: string | null;
}

export interface TaskStatusUpdateResponse {
  task_id: string;
  status: string;
  updated_at: string;
}

export function getTasks(
  accessToken: string,
  query: TaskListQuery = {},
): Promise<TaskListResponse> {
  return request<TaskListResponse>({
    url: API_ENDPOINTS.tasks.list,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getTaskDetail(
  accessToken: string,
  taskId: string,
): Promise<TaskDetailDto> {
  return request<TaskDetailDto>({
    url: API_ENDPOINTS.tasks.detail(taskId),
    method: "GET",
    token: accessToken,
  });
}

export function getAdminTaskDetail(
  accessToken: string,
  taskId: string,
): Promise<TaskDetailDto> {
  return request<TaskDetailDto>({
    url: API_ENDPOINTS.admin.task(taskId),
    method: "GET",
    token: accessToken,
  });
}

export function publishSummerFeedingTask(
  payload: SummerFeedingTaskCreatePayload,
  accessToken: string,
): Promise<SummerFeedingTaskCreateResponse> {
  return request<
    SummerFeedingTaskCreateResponse,
    SummerFeedingTaskCreatePayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.admin.summerFeedingTask,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateSummerFeedingTask(
  accessToken: string,
  taskId: string,
  payload: SummerFeedingTaskCreatePayload,
): Promise<SummerFeedingTaskUpdateResponse> {
  return request<
    SummerFeedingTaskUpdateResponse,
    SummerFeedingTaskCreatePayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.admin.task(taskId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateSummerFeedingTaskStatus(
  accessToken: string,
  taskId: string,
  payload: TaskStatusUpdatePayload,
): Promise<TaskStatusUpdateResponse> {
  return request<
    TaskStatusUpdateResponse,
    TaskStatusUpdatePayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.admin.taskStatus(taskId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function checkinTask(
  accessToken: string,
  taskId: string,
  payload: TaskCheckinPayload,
): Promise<TaskCheckinResponse> {
  return request<TaskCheckinResponse, TaskCheckinPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.tasks.checkins(taskId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}
