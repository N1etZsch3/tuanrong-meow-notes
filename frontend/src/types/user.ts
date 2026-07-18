import type { TitleShield, UserTitle } from "@/constants/titles";

export type UserRole = "member" | "summer_volunteer" | "admin" | "super_admin";

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
  departments?: string[];
  contact_info?: string | null;
  title?: UserTitle;
  title_label?: string | null;
  title_shield?: TitleShield | null;
}
