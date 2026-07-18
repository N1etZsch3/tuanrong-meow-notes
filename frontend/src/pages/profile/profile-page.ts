import type { MeDashboardStats } from "@/api/me";

export type ProfileRecordType =
  | "total_tasks"
  | "monthly_completed"
  | "in_progress"
  | "observations"
  | "favorite_cats";

export const PROFILE_RECORD_TYPES: Record<
  ProfileRecordType,
  { title: string; empty_title: string; empty_description: string }
> = {
  total_tasks: {
    title: "累计任务",
    empty_title: "还没有任务记录",
    empty_description: "参与或完成任务后，记录会出现在这里。",
  },
  monthly_completed: {
    title: "本月完成",
    empty_title: "本月还没有完成任务",
    empty_description: "完成打卡后，本月任务会自动归档。",
  },
  in_progress: {
    title: "进行中",
    empty_title: "当前没有进行中的任务",
    empty_description: "接取任务后，可以从这里快速查看。",
  },
  observations: {
    title: "观察记录",
    empty_title: "还没有观察记录",
    empty_description: "提交猫咪观察后，记录会在这里沉淀。",
  },
  favorite_cats: {
    title: "收藏猫咪",
    empty_title: "还没有收藏猫咪",
    empty_description: "收藏喜欢关注的猫咪后，可以从这里快速查看。",
  },
};

export const PROFILE_STAT_ENTRIES = [
  {
    key: "total_completed_tasks",
    label: "累计任务",
    color: "green",
    icon: "✓",
    recordType: "total_tasks",
  },
  {
    key: "monthly_completed_tasks",
    label: "本月完成",
    color: "blue",
    icon: "✓",
    recordType: "monthly_completed",
  },
  {
    key: "current_in_progress_tasks",
    label: "进行中",
    color: "orange",
    icon: "⌛",
    recordType: "in_progress",
  },
  {
    key: "total_observation_records",
    label: "观察记录",
    color: "purple",
    icon: "◉",
    recordType: "observations",
  },
] as const;

export function getStatValue(
  stats: MeDashboardStats | null,
  key: (typeof PROFILE_STAT_ENTRIES)[number]["key"],
): number {
  return stats?.[key] ?? 0;
}

export function getRoleLabel(role: string | undefined): string {
  if (role === "super_admin") {
    return "超级管理员";
  }
  if (role === "admin") {
    return "猫协管理员";
  }
  if (role === "summer_volunteer") {
    return "暑期志愿者";
  }
  return "猫协成员";
}

export function getRolePillClass(role: string | undefined): string {
  if (role === "admin" || role === "super_admin") {
    return "role-pill--admin";
  }
  if (role === "summer_volunteer") {
    return "role-pill--volunteer";
  }
  return "role-pill--member";
}

export function buildRecordRoute(type: ProfileRecordType): string {
  return `/pages/profile/records?type=${type}`;
}
