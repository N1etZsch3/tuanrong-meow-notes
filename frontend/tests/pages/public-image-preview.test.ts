import { afterEach, describe, expect, it, vi } from "vitest";

import catDetailSource from "../../src/pages/public/cat-detail.vue?raw";
import imagePreviewSource from "../../src/pages/public/image-preview.ts?raw";
import postDetailSource from "../../src/pages/public/post-detail.vue?raw";
import { previewPublicImage } from "../../src/pages/public/image-preview";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("public native image preview", () => {
  it("opens the requested image through the native preview API and removes duplicates", () => {
    const previewImage = vi.fn();
    vi.stubGlobal("uni", { previewImage });

    previewPublicImage("https://img.example/b.jpg", [
      "https://img.example/a.jpg",
      "https://img.example/b.jpg",
      "https://img.example/a.jpg",
    ]);

    expect(previewImage).toHaveBeenCalledWith({
      current: "https://img.example/b.jpg",
      urls: ["https://img.example/a.jpg", "https://img.example/b.jpg"],
    });
  });

  it("does not call the preview API when there are no usable images", () => {
    const previewImage = vi.fn();
    vi.stubGlobal("uni", { previewImage });

    previewPublicImage(null, [null, undefined, ""]);

    expect(previewImage).not.toHaveBeenCalled();
  });

  it("wires cat albums and post images to the shared native preview helper", () => {
    expect(imagePreviewSource).toContain("uni.previewImage({");
    expect(catDetailSource).toContain('@tap="previewPhoto(photo.file_url)"');
    expect(catDetailSource).toContain('@tap="previewPhoto(photos[0].file_url)"');
    expect(postDetailSource).toContain('@tap="previewPostImage(post.cover_url)"');
    expect(postDetailSource).toContain('@tap="previewPostImage(block.image_url)"');
    expect(catDetailSource).toContain("previewPublicImage(");
    expect(postDetailSource).toContain("previewPublicImage(imageUrl, previewImageUrls.value)");
  });
});
