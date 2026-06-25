import { describe, expect, it, vi } from "vitest";

import { completeProfile, getMyProfile, updateMyProfile } from "@/api/profile";

describe("profile api", () => {
  it("gets current profile through /profile/me", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            user_id: "u1",
            meow_no: "trmx0001",
            student_no: "trmx0001",
            role: "member",
            nickname: "小林",
            avatar_url: null,
            department: null,
            contact_info: null,
            profile_completed: false,
            profile_completed_at: null,
          },
          trace_id: "trace-profile",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getMyProfile("token-1")).resolves.toEqual(
      expect.objectContaining({
        meow_no: "trmx0001",
        profile_completed: false,
      }),
    );
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/profile/me"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });

  it("completes profile initialization through /profile/me/complete", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            profile_completed: true,
            next_action: "enter_app",
          },
          trace_id: "trace-complete",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(
      completeProfile(
        {
          nickname: "喂猫搭子🥜",
          avatar_url: null,
          department: "生存保障部",
          contact_info: "13800138000",
        },
        "token-1",
      ),
    ).resolves.toEqual({
      profile_completed: true,
      next_action: "enter_app",
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/profile/me/complete"),
        data: expect.objectContaining({
          department: "生存保障部",
          contact_info: "13800138000",
        }),
      }),
    );
  });

  it("updates current profile through PATCH /profile/me", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            user_id: "u1",
            meow_no: "trmx0001",
            student_no: "trmx0001",
            role: "member",
            nickname: "巡查搭子",
            avatar_url: "/uploads/avatar/u1.jpg",
            department: "活动部",
            contact_info: "13900139000",
            profile_completed: true,
            profile_completed_at: "2026-06-25T10:00:00+08:00",
          },
          trace_id: "trace-update-profile",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(
      updateMyProfile(
        {
          nickname: "巡查搭子",
          avatar_url: "/uploads/avatar/u1.jpg",
          department: "活动部",
          contact_info: "13900139000",
        },
        "token-1",
      ),
    ).resolves.toMatchObject({
      nickname: "巡查搭子",
      department: "活动部",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/profile/me"),
        data: expect.objectContaining({
          nickname: "巡查搭子",
          contact_info: "13900139000",
        }),
        header: expect.objectContaining({ Authorization: "Bearer token-1" }),
      }),
    );
  });
});
