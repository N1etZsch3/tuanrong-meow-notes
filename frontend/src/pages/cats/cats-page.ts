import type { CatListQuery, CatStatsResponse } from "@/api/cats";

export const EMPTY_CAT_STATS: CatStatsResponse = {
  total_cats: 0,
  active_cats: 0,
  waiting_adoption_cats: 0,
  watching_cats: 0,
  neutered_cats: 0,
  neuter_rate: 0,
};

export interface CatListQueryInput {
  keyword: string;
  filter_key: string;
  filter_value: string;
  sort: string;
  page: number;
  page_size: number;
}

export type CatTagTone = "green" | "blue" | "orange" | "red" | "purple" | "gray";

export function normalizeCatStats(stats: CatStatsResponse | null): CatStatsResponse {
  return stats ?? EMPTY_CAT_STATS;
}

export function buildCatListQuery(input: CatListQueryInput): CatListQuery {
  const query: CatListQuery = {
    sort: input.sort,
    page: input.page,
    page_size: input.page_size,
  };
  const keyword = input.keyword.trim();
  if (keyword) {
    query.keyword = keyword;
  }
  if (input.filter_key && input.filter_value) {
    query.filter_key = input.filter_key;
    query.filter_value = input.filter_value;
  }
  return query;
}

function startOfLocalDay(value: Date): number {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate()).getTime();
}

function padTime(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatCatSeenTime(value: string | null, now = new Date()): string {
  if (!value) {
    return "未知";
  }
  const seenAt = new Date(value);
  if (Number.isNaN(seenAt.getTime())) {
    return "未知";
  }

  const dayDiff = Math.floor(
    (startOfLocalDay(now) - startOfLocalDay(seenAt)) / (24 * 60 * 60 * 1000),
  );
  const timeText = `${padTime(seenAt.getHours())}:${padTime(seenAt.getMinutes())}`;
  if (dayDiff === 0) {
    return `今天 ${timeText}`;
  }
  if (dayDiff === 1) {
    return `昨天 ${timeText}`;
  }
  if (dayDiff > 1 && dayDiff <= 7) {
    return `${dayDiff}天前`;
  }
  return `${seenAt.getMonth() + 1}月${seenAt.getDate()}日`;
}

export function getCatTagTone(tag: string): CatTagTone {
  if (["健康", "已恢复"].includes(tag)) {
    return "green";
  }
  if (["已绝育", "已预约"].includes(tag)) {
    return "blue";
  }
  if (["待观察", "异常", "疑似生病", "治疗中", "暂时失踪", "待领养"].includes(tag)) {
    return "orange";
  }
  if (["受伤", "未绝育", "已死亡"].includes(tag)) {
    return "red";
  }
  if (["亲人", "温顺", "活泼", "贪吃"].includes(tag)) {
    return "purple";
  }
  return "gray";
}
