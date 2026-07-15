import { describe, expect, it } from "vitest";

import {
  DELETED_ACCOUNT_EXISTS,
  parseDeletedAccountConflict,
} from "../../src/pages/admin/deleted-account-restore";
import { ApiBusinessError } from "../../src/services/request";

describe("deleted account restore conflict", () => {
  it("parses a restorable deleted account response", () => {
    const result = parseDeletedAccountConflict(
      new ApiBusinessError(
        DELETED_ACCOUNT_EXISTS,
        "该喵喵号曾被使用，可重新启用原账号",
        "trace-restore",
        {
          conflict_type: "deleted_account",
          user_id: "u-deleted",
          meow_no: "trmx1234",
          nickname: "团团",
          deleted_at: "2026-07-15T08:00:00+00:00",
          can_restore: true,
        },
      ),
    );

    expect(result).toEqual({
      user_id: "u-deleted",
      meow_no: "trmx1234",
      nickname: "团团",
      deleted_at: "2026-07-15T08:00:00+00:00",
    });
  });

  it("rejects unrelated or malformed business errors", () => {
    expect(
      parseDeletedAccountConflict(
        new ApiBusinessError(40901, "喵喵号已存在", "trace-active", null),
      ),
    ).toBeNull();
    expect(
      parseDeletedAccountConflict(
        new ApiBusinessError(DELETED_ACCOUNT_EXISTS, "conflict", "trace-malformed", {
          conflict_type: "deleted_account",
          can_restore: false,
        }),
      ),
    ).toBeNull();
  });
});
