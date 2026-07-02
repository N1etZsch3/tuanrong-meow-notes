import { request } from "@/services/request";
import { API_ENDPOINTS } from "@/api/routes";
import type { UserRole, UserStatus } from "@/types/user";

export interface AdminUserProfilePayload {
  nickname?: string;
  real_name?: string | null;
  department?: string | null;
  grade?: string | null;
  joined_at?: string | null;
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
