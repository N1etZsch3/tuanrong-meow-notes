import { ApiBusinessError } from "@/services/request";

export const DELETED_ACCOUNT_EXISTS = 40904;

export interface DeletedAccountConflict {
  user_id: string;
  meow_no: string;
  nickname: string;
  deleted_at: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}

export function parseDeletedAccountConflict(error: unknown): DeletedAccountConflict | null {
  if (!(error instanceof ApiBusinessError) || error.code !== DELETED_ACCOUNT_EXISTS) {
    return null;
  }
  if (!isRecord(error.data)) {
    return null;
  }

  const data = error.data;
  if (
    data.conflict_type !== "deleted_account" ||
    data.can_restore !== true ||
    typeof data.user_id !== "string" ||
    typeof data.meow_no !== "string" ||
    typeof data.nickname !== "string" ||
    typeof data.deleted_at !== "string"
  ) {
    return null;
  }

  return {
    user_id: data.user_id,
    meow_no: data.meow_no,
    nickname: data.nickname,
    deleted_at: data.deleted_at,
  };
}
