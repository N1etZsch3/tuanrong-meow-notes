import { request } from "@/services/request";
import { API_ENDPOINTS } from "@/api/routes";
import type { UserRole } from "@/types/user";

export type ProfileNextAction = "enter_app";

export interface MyProfileResponse {
  user_id: string;
  student_no: string;
  meow_no: string;
  role: UserRole;
  nickname: string;
  avatar_url: string | null;
  department: string | null;
  contact_info: string | null;
  profile_completed: boolean;
  profile_completed_at: string | null;
}

export interface CompleteProfilePayload {
  nickname: string;
  avatar_url?: string | null;
  department: string;
  contact_info: string;
}

export interface UpdateProfilePayload {
  nickname?: string;
  avatar_url?: string | null;
  department?: string;
  contact_info?: string | null;
}

export interface CompleteProfileResponse {
  profile_completed: boolean;
  next_action: ProfileNextAction;
}

export function getMyProfile(accessToken: string): Promise<MyProfileResponse> {
  return request<MyProfileResponse>({
    url: API_ENDPOINTS.profile.me,
    method: "GET",
    token: accessToken,
  });
}

export function completeProfile(
  payload: CompleteProfilePayload,
  accessToken: string,
): Promise<CompleteProfileResponse> {
  return request<CompleteProfileResponse, CompleteProfilePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.profile.complete,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateMyProfile(
  payload: UpdateProfilePayload,
  accessToken: string,
): Promise<MyProfileResponse> {
  return request<MyProfileResponse, UpdateProfilePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.profile.me,
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}
