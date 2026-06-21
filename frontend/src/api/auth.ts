import { request } from "@/services/request";
import type { CurrentUser, UserRole, UserStatus } from "@/types/user";

export interface CaptchaResponse {
  captcha_id: string;
  captcha_image: string;
  expires_in: number;
}

export interface LoginPayload {
  student_no: string;
  password: string;
  captcha_id: string;
  captcha_code: string;
  agree_terms: boolean;
}

export interface LoginUser {
  id: string;
  student_no: string;
  nickname: string;
  avatar_url: string | null;
  role: UserRole;
  status: UserStatus;
}

export interface LoginResponse {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  must_change_password: boolean;
  user: LoginUser;
}

export interface CurrentUserResponse {
  id: string;
  student_no: string;
  role: UserRole;
  status: UserStatus;
  must_change_password: boolean;
  profile: {
    nickname: string;
    avatar_url: string | null;
    real_name?: string;
    department?: string;
    grade?: string;
  };
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export function getCaptcha(): Promise<CaptchaResponse> {
  return request<CaptchaResponse>({
    url: "/auth/captcha",
    method: "GET",
  });
}

export function login(payload: LoginPayload): Promise<LoginResponse> {
  return request<LoginResponse, LoginPayload & Record<string, unknown>>({
    url: "/auth/login",
    method: "POST",
    data: { ...payload },
  });
}

export function getCurrentUser(accessToken: string): Promise<CurrentUserResponse> {
  return request<CurrentUserResponse>({
    url: "/auth/me",
    method: "GET",
    token: accessToken,
  });
}

export function changePassword(
  payload: ChangePasswordPayload,
  accessToken: string,
): Promise<null> {
  return request<null, ChangePasswordPayload & Record<string, unknown>>({
    url: "/auth/password",
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function logout(accessToken: string): Promise<null> {
  return request<null>({
    url: "/auth/logout",
    method: "POST",
    token: accessToken,
  });
}

export function normalizeLoginUser(response: LoginResponse): CurrentUser {
  return {
    ...response.user,
    must_change_password: response.must_change_password,
  };
}

export function normalizeCurrentUser(response: CurrentUserResponse): CurrentUser {
  return {
    id: response.id,
    student_no: response.student_no,
    role: response.role,
    status: response.status,
    nickname: response.profile.nickname,
    avatar_url: response.profile.avatar_url,
    must_change_password: response.must_change_password,
  };
}
