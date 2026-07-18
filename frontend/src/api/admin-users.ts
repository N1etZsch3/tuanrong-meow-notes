import { request } from "@/services/request";
import {
  API_ENDPOINTS,
  compactApiParams,
  compactDefinedApiParams,
} from "@/api/routes";
import type { UserRole, UserStatus } from "@/types/user";
import type { TitleShield, UserTitle } from "@/constants/titles";

export interface AdminUserProfilePayload {
  nickname?: string;
  avatar_url?: string | null;
  real_name?: string | null;
  department?: string | null;
  departments?: string[];
  grade?: string | null;
  joined_at?: string | null;
  contact_info?: string | null;
  title?: UserTitle;
}

export interface AdminCreateUserPayload {
  meow_no?: string;
  student_no?: string;
  initial_password?: string;
  role?: UserRole;
  profile?: AdminUserProfilePayload;
  must_change_password?: boolean;
}

export interface AdminCreateUserResponse {
  id: string;
  student_no: string;
  meow_no: string;
  role: UserRole;
  status: UserStatus;
  must_change_password: boolean;
}

export interface AdminRestoreUserPayload {
  initial_password?: string;
}

export interface AdminRestoreUserResponse extends AdminCreateUserResponse {
  nickname: string;
  wechat_bound: boolean;
}

export interface AdminUserProfileDto {
  nickname: string;
  avatar_url: string | null;
  avatar_review_asset_id?: string | null;
  avatar_review_status?: "idle" | "pending" | "passed" | "rejected" | "failed";
  real_name: string | null;
  department: string | null;
  departments: string[];
  grade: string | null;
  contact_info: string | null;
  title: UserTitle;
  title_label: string | null;
  title_shield: TitleShield | null;
}

export interface AdminUserDto {
  id: string;
  student_no: string;
  meow_no: string;
  role: UserRole | string;
  status: UserStatus | string;
  must_change_password: boolean;
  profile_completed: boolean;
  last_login_at: string | null;
  wechat_bound: boolean;
  profile: AdminUserProfileDto;
  editable?: boolean;
  can_reset_password?: boolean;
}

export interface AdminUserListQuery {
  page?: number;
  page_size?: number;
  keyword?: string;
  role?: string;
  status?: string;
  department?: string;
  sort_by?: "meow_no";
  sort_order?: "asc" | "desc";
}

export interface AdminUserListResponse {
  items: AdminUserDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface AdminUpdateUserPayload {
  role?: string;
  status?: string;
  profile?: AdminUserProfilePayload;
}

export interface AdminResetPasswordPayload {
  new_password: string;
  must_change_password?: boolean;
}

export interface AdminResetPasswordResponse {
  user_id: string;
  must_change_password: boolean;
}

export interface AdminClearWeChatBindingResponse {
  user_id: string;
  wechat_bound: boolean;
  token_version: number;
}

export interface AdminDeleteUserResponse {
  user_id: string;
  status: UserStatus | string;
  deleted_at: string | null;
}

export function createAdminUser(
  payload: AdminCreateUserPayload,
  accessToken: string,
): Promise<AdminCreateUserResponse> {
  return request<AdminCreateUserResponse, AdminCreateUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.users,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function createSuperAdminUser(
  payload: AdminCreateUserPayload,
  accessToken: string,
): Promise<AdminCreateUserResponse> {
  return request<AdminCreateUserResponse, AdminCreateUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.superAdmin.admins,
    method: "POST",
    data: { ...payload, role: "admin" },
    token: accessToken,
  });
}

export function restoreAdminUser(
  accessToken: string,
  userId: string,
  payload: AdminRestoreUserPayload,
): Promise<AdminRestoreUserResponse> {
  return request<AdminRestoreUserResponse, AdminRestoreUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.userRestore(userId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function restoreSuperAdminUser(
  accessToken: string,
  userId: string,
  payload: AdminRestoreUserPayload,
): Promise<AdminRestoreUserResponse> {
  return request<AdminRestoreUserResponse, AdminRestoreUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.superAdmin.userRestore(userId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function listAdminUsers(
  accessToken: string,
  query: AdminUserListQuery = {},
): Promise<AdminUserListResponse> {
  return request<AdminUserListResponse>({
    url: API_ENDPOINTS.admin.users,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getAdminUserDetail(
  accessToken: string,
  userId: string,
): Promise<AdminUserDto> {
  return request<AdminUserDto>({
    url: API_ENDPOINTS.admin.user(userId),
    method: "GET",
    token: accessToken,
  });
}

export function updateAdminUser(
  accessToken: string,
  userId: string,
  payload: AdminUpdateUserPayload,
): Promise<AdminUserDto> {
  return request<AdminUserDto, AdminUpdateUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.user(userId),
    method: "PATCH",
    data: compactDefinedApiParams(payload),
    token: accessToken,
  });
}

export function updateSuperAdminUser(
  accessToken: string,
  userId: string,
  payload: AdminUpdateUserPayload,
): Promise<AdminUserDto> {
  return request<AdminUserDto, AdminUpdateUserPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.superAdmin.user(userId),
    method: "PATCH",
    data: compactDefinedApiParams(payload),
    token: accessToken,
  });
}

export function resetAdminUserPassword(
  accessToken: string,
  userId: string,
  payload: AdminResetPasswordPayload,
): Promise<AdminResetPasswordResponse> {
  return request<AdminResetPasswordResponse, AdminResetPasswordPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.admin.userResetPassword(userId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function resetSuperAdminUserPassword(
  accessToken: string,
  userId: string,
  payload: AdminResetPasswordPayload,
): Promise<AdminResetPasswordResponse> {
  return request<AdminResetPasswordResponse, AdminResetPasswordPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.superAdmin.userResetPassword(userId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function clearAdminUserWechatBinding(
  accessToken: string,
  userId: string,
): Promise<AdminClearWeChatBindingResponse> {
  return request<AdminClearWeChatBindingResponse>({
    url: API_ENDPOINTS.admin.userWechatBinding(userId),
    method: "DELETE",
    token: accessToken,
  });
}

export function clearSuperAdminUserWechatBinding(
  accessToken: string,
  userId: string,
): Promise<AdminClearWeChatBindingResponse> {
  return request<AdminClearWeChatBindingResponse>({
    url: API_ENDPOINTS.superAdmin.userWechatBinding(userId),
    method: "DELETE",
    token: accessToken,
  });
}

export function deleteAdminUser(
  accessToken: string,
  userId: string,
): Promise<AdminDeleteUserResponse> {
  return request<AdminDeleteUserResponse>({
    url: API_ENDPOINTS.admin.user(userId),
    method: "DELETE",
    token: accessToken,
  });
}

export function deleteSuperAdminUser(
  accessToken: string,
  userId: string,
): Promise<AdminDeleteUserResponse> {
  return request<AdminDeleteUserResponse>({
    url: API_ENDPOINTS.superAdmin.user(userId),
    method: "DELETE",
    token: accessToken,
  });
}
