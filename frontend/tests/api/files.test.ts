import { describe, expect, it, vi } from "vitest";

import { buildFileAssetContentUrl, uploadImage } from "@/api/files";

describe("files api", () => {
  it("builds a mini-program image-safe asset content url", () => {
    expect(buildFileAssetContentUrl("asset-1", "task_list_cover")).toBe(
      "http://localhost:8000/api/v1/files/assets/asset-1/content?scene=task_list_cover",
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
});
