import { describe, expect, it, vi } from "vitest";

import { createAdminUser } from "@/api/admin-users";

describe("admin users api", () => {
  it("creates a member account through /admin/users", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "成员账号创建成功",
          data: {
            id: "u1",
            student_no: "trmx0001",
            meow_no: "trmx0001",
            role: "member",
            status: "active",
            must_change_password: true,
          },
          trace_id: "trace-admin-user",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(
      createAdminUser(
        {
          role: "member",
          profile: {
            nickname: "",
            department: "生存保障部",
          },
          must_change_password: true,
        },
        "admin-token",
      ),
    ).resolves.toMatchObject({
      meow_no: "trmx0001",
      must_change_password: true,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/admin/users"),
        data: expect.objectContaining({
          role: "member",
          profile: expect.objectContaining({ department: "生存保障部" }),
        }),
        header: expect.objectContaining({ Authorization: "Bearer admin-token" }),
      }),
    );
  });
});
