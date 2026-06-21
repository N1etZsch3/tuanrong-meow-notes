export type UserRole = "member" | "admin" | "super_admin";

export type UserStatus = "active" | "inactive" | "blocked" | "left" | "deleted";

export interface CurrentUser {
  id: string;
  student_no: string;
  role: UserRole;
  status: UserStatus;
  nickname: string;
  avatar_url: string;
  must_change_password: boolean;
}
