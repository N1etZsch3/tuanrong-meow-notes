export type UserRole = "member" | "admin" | "super_admin";

export type UserStatus = "active" | "inactive" | "blocked" | "left" | "deleted";

export interface CurrentUser {
  id: string;
  student_no: string;
  meow_no?: string;
  role: UserRole;
  status: UserStatus;
  nickname: string;
  avatar_url: string | null;
  must_change_password: boolean;
  profile_completed: boolean;
  department?: string | null;
  contact_info?: string | null;
}
