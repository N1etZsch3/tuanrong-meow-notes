import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildFileAssetContentUrl,
  deleteImageAsset,
  uploadImage,
  uploadUserAvatar,
} from "@/api/files";
import { appEnv } from "@/config/app-env";

function mockSuccess(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-file",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("files api", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("builds a mini-program image-safe asset content url", () => {
    expect(buildFileAssetContentUrl("asset-1", "task_list_cover")).toBe(
      `${appEnv.apiBaseUrl}/files/assets/asset-1/content?scene=task_list_cover`,
    );
  });

  it("builds asset content urls without browser URLSearchParams", () => {
    vi.stubGlobal("URLSearchParams", undefined);

    expect(buildFileAssetContentUrl("asset-1", "task detail full")).toBe(
      `${appEnv.apiBaseUrl}/files/assets/asset-1/content?scene=task%20detail%20full`,
    );
  });

  it("uploads an image through uni.uploadFile with bearer token and form data", async () => {
    const uploadFile = vi.fn((options: UniNamespace.UploadFileOption) => {
      options.success?.({
        statusCode: 200,
        data: JSON.stringify({
          code: 0,
          message: "success",
          data: {
            asset_id: "asset-1",
            default_url: "/uploads/task/asset-1.jpg",
            default_thumb_url: "/uploads/task/asset-1-thumb.jpg",
          },
          trace_id: "trace-file",
        }),
        header: {},
        cookies: [],
      } as UniNamespace.UploadFileSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { uploadFile });

    await expect(
      uploadImage("token-1", "/tmp/task-point.jpg", {
        usage_type: "map_point_scene",
        owner_type: "task",
        visibility: "internal",
        caption: "任务点图片",
      }),
    ).resolves.toMatchObject({
      asset_id: "asset-1",
      default_url: "/uploads/task/asset-1.jpg",
    });

    expect(uploadFile).toHaveBeenCalledWith(
      expect.objectContaining({
        filePath: "/tmp/task-point.jpg",
        name: "file",
        url: expect.stringContaining("/files/images"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
        formData: {
          usage_type: "map_point_scene",
          owner_type: "task",
          visibility: "internal",
          caption: "任务点图片",
        },
      }),
    );
  });

  it("adds a fresh WeChat code for server-side image review", async () => {
    const uploadFile = vi.fn((options: UniNamespace.UploadFileOption) => {
      options.success?.({
        statusCode: 200,
        data: JSON.stringify({
          code: 0,
          message: "success",
          data: {
            asset_id: "asset-pending",
            default_url: null,
            default_thumb_url: null,
            security_status: "pending",
          },
          trace_id: "trace-file",
        }),
        header: {},
        cookies: [],
      } as UniNamespace.UploadFileSuccessCallbackResult);
    });
    const login = vi.fn((options: UniNamespace.LoginOptions) => {
      options.success?.({ code: "wechat-code-1", errMsg: "login:ok", authResult: "" });
    });
    vi.stubGlobal("uni", { login, uploadFile });

    await uploadUserAvatar("token-1", "/tmp/avatar.jpg", "user-1");

    expect(uploadFile).toHaveBeenCalledWith(
      expect.objectContaining({
        formData: expect.objectContaining({
          usage_type: "user_avatar",
          wechat_code: "wechat-code-1",
        }),
      }),
    );
  });

  it("waits for non-avatar image approval before returning a publishable URL", async () => {
    vi.useFakeTimers();
    const uploadFile = vi.fn((options: UniNamespace.UploadFileOption) => {
      options.success?.({
        statusCode: 200,
        data: JSON.stringify({
          code: 0,
          message: "success",
          data: {
            asset_id: "asset-business-pending",
            default_url: null,
            default_thumb_url: null,
            security_status: "pending",
          },
          trace_id: "trace-upload",
        }),
        header: {},
        cookies: [],
      } as UniNamespace.UploadFileSuccessCallbackResult);
    });
    const requestMock = mockSuccess({
      asset_id: "asset-business-pending",
      default_url: "https://approved.example/display.jpg",
      default_thumb_url: "https://approved.example/thumb.jpg",
      security_status: "passed",
    });
    vi.stubGlobal("uni", { uploadFile, request: requestMock });

    const resultPromise = uploadImage("token-1", "/tmp/checkin.jpg", {
      usage_type: "task_checkin_photo",
    });
    await vi.advanceTimersByTimeAsync(1000);

    await expect(resultPromise).resolves.toMatchObject({
      security_status: "passed",
      default_url: "https://approved.example/display.jpg",
    });
    vi.useRealTimers();
  });

  it("soft deletes an uploaded image asset with bearer token", async () => {
    const requestMock = mockSuccess({
      asset_id: "asset-1",
      deleted: true,
      deleted_at: "2026-07-03T15:20:00+08:00",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await deleteImageAsset("token-1", "asset-1");

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "DELETE",
        url: expect.stringContaining("/files/assets/asset-1"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });
});
