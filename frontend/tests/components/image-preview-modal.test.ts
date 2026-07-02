import { describe, expect, it } from "vitest";

import imagePreviewModalSource from "../../src/components/ImagePreviewModal.vue?raw";

describe("image preview modal", () => {
  it("renders an in-app zoomable image viewer with a close button", () => {
    expect(imagePreviewModalSource).toContain('class="image-preview-modal"');
    expect(imagePreviewModalSource).toContain("<movable-area");
    expect(imagePreviewModalSource).toContain("<movable-view");
    expect(imagePreviewModalSource).toContain(":scale=\"true\"");
    expect(imagePreviewModalSource).toContain(":scale-min=\"1\"");
    expect(imagePreviewModalSource).toContain(":scale-max=\"4\"");
    expect(imagePreviewModalSource).toContain("关闭");
    expect(imagePreviewModalSource).toContain("emit(\"close\")");
  });

  it("supports switching between multiple preview images inside the app", () => {
    expect(imagePreviewModalSource).toContain("showPrevious");
    expect(imagePreviewModalSource).toContain("showNext");
    expect(imagePreviewModalSource).toContain("activeIndex");
    expect(imagePreviewModalSource).toContain("emit(\"change\"");
    expect(imagePreviewModalSource).not.toContain("uni.previewImage");
  });

  it("keeps the close button and counter below the phone status area", () => {
    expect(imagePreviewModalSource).toContain(
      "top: calc(env(safe-area-inset-top) + 170rpx);",
    );
    expect(imagePreviewModalSource).not.toContain(
      "top: calc(env(safe-area-inset-top) + 28rpx);",
    );
  });
});
