import { request } from "@/services/request";
import { API_ENDPOINTS } from "@/api/routes";
import type { CurrentUser, UserRole, UserStatus } from "@/types/user";

export interface CaptchaResponse {
  captcha_id: string;
  captcha_image: string;
  expires_in: number;
}

export interface LoginPayload {
  meow_no?: string;
  student_no?: string;
  password: string;
  captcha_id: string;
  captcha_code: string;
  agree_terms: boolean;
  wechat_code?: string;
  agree_wechat_bind?: boolean;
}

export interface LoginUser {
  id: string;
  student_no: string;
  meow_no?: string;
  nickname: string;
  avatar_url: string | null;
  role: UserRole;
  status: UserStatus;
  profile_completed: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  must_change_password: boolean;
  profile_completed?: boolean;
  next_action: "change_password" | "complete_profile" | "enter_app";
  user: LoginUser;
}

export interface RenewAccessTokenResponse {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
}

export interface CurrentUserResponse {
  id: string;
  student_no: string;
  meow_no?: string;
  role: UserRole;
  status: UserStatus;
  must_change_password: boolean;
  profile_completed: boolean;
  profile: {
    nickname: string;
    avatar_url: string | null;
    real_name?: string;
    department?: string;
    departments?: string[];
    grade?: string;
    contact_info?: string | null;
  };
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ChangePasswordResponse {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  must_change_password: boolean;
  profile_completed: boolean;
  token_invalidated: boolean;
  next_action: "complete_profile" | "enter_app";
}

export interface UnbindWeChatBindingResponse {
  user_id: string;
  wechat_bound: false;
  token_version: number;
  token_invalidated: true;
}

export function getCaptcha(): Promise<CaptchaResponse> {
  return request<CaptchaResponse>({
    url: API_ENDPOINTS.auth.captcha,
    method: "GET",
  });
}

export function login(payload: LoginPayload): Promise<LoginResponse> {
  return request<LoginResponse, LoginPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.auth.login,
    method: "POST",
    data: { ...payload },
  });
}

export function wechatLogin(code: string): Promise<LoginResponse> {
  return request<LoginResponse, { code: string }>({
    url: API_ENDPOINTS.auth.wechatLogin,
    method: "POST",
    data: { code },
  });
}

export function renewAccessToken(
  accessToken: string,
): Promise<RenewAccessTokenResponse> {
  return request<RenewAccessTokenResponse>({
    url: API_ENDPOINTS.auth.renew,
    method: "POST",
    token: accessToken,
  });
}

export function getCurrentUser(accessToken: string): Promise<CurrentUserResponse> {
  return request<CurrentUserResponse>({
    url: API_ENDPOINTS.auth.me,
    method: "GET",
    token: accessToken,
  });
}

export function changePassword(
  payload: ChangePasswordPayload,
  accessToken: string,
): Promise<ChangePasswordResponse> {
  return request<ChangePasswordResponse, ChangePasswordPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.auth.password,
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function unbindWechatBinding(
  accessToken: string,
): Promise<UnbindWeChatBindingResponse> {
  return request<UnbindWeChatBindingResponse>({
    url: API_ENDPOINTS.auth.wechatBinding,
    method: "DELETE",
    token: accessToken,
  });
}

export function logout(accessToken: string): Promise<null> {
  return request<null>({
    url: API_ENDPOINTS.auth.logout,
    method: "POST",
    token: accessToken,
  });
}

export function normalizeLoginUser(response: LoginResponse): CurrentUser {
  return {
    ...response.user,
    meow_no: response.user.meow_no || response.user.student_no,
    must_change_password: response.must_change_password,
    profile_completed: response.user.profile_completed,
  };
}

export function normalizeCurrentUser(response: CurrentUserResponse): CurrentUser {
  return {
    id: response.id,
    student_no: response.student_no,
    meow_no: response.meow_no || response.student_no,
    role: response.role,
    status: response.status,
    nickname: response.profile.nickname,
    avatar_url: response.profile.avatar_url,
    must_change_password: response.must_change_password,
    profile_completed: response.profile_completed,
    department: response.profile.department ?? null,
    departments: response.profile.departments ?? [],
    contact_info: response.profile.contact_info ?? null,
  };
}
