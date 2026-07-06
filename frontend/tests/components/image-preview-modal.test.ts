import { describe, expect, it } from "vitest";

import imagePreviewModalSource from "../../src/components/ImagePreviewModal.vue?raw";

describe("image preview modal", () => {
  it("renders an in-app zoomable image viewer with a counter", () => {
    expect(imagePreviewModalSource).toContain('class="image-preview-modal"');
    expect(imagePreviewModalSource).toContain("<movable-area");
    expect(imagePreviewModalSource).toContain("<movable-view");
    expect(imagePreviewModalSource).toContain(":scale=\"true\"");
    expect(imagePreviewModalSource).toContain(":scale-min=\"1\"");
    expect(imagePreviewModalSource).toContain(":scale-max=\"4\"");
    expect(imagePreviewModalSource).toContain("image-preview-count");
    expect(imagePreviewModalSource).not.toContain("关闭");
    expect(imagePreviewModalSource).not.toContain("image-preview-close");
  });

  it("closes when tapping the non-image backdrop area", () => {
    expect(imagePreviewModalSource).toContain('class="image-preview-backdrop"');
    expect(imagePreviewModalSource).toContain('@tap="close"');
    expect(imagePreviewModalSource).toContain("emit(\"close\")");
  });

  it("supports swiping between multiple preview images inside the app", () => {
    expect(imagePreviewModalSource).toContain('@touchstart="handlePreviewTouchStart"');
    expect(imagePreviewModalSource).toContain('@touchend="handlePreviewTouchEnd"');
    expect(imagePreviewModalSource).toContain("showPrevious");
    expect(imagePreviewModalSource).toContain("showNext");
    expect(imagePreviewModalSource).toContain("activeIndex");
    expect(imagePreviewModalSource).toContain("emit(\"change\"");
    expect(imagePreviewModalSource).not.toContain("uni.previewImage");
  });

  it("does not render side pagination buttons in the large image viewer", () => {
    expect(imagePreviewModalSource).not.toContain("image-preview-nav");
    expect(imagePreviewModalSource).not.toContain("image-preview-prev");
    expect(imagePreviewModalSource).not.toContain("image-preview-next");
    expect(imagePreviewModalSource).not.toContain("image-preview-button-hover");
  });

  it("keeps the counter below the phone status area", () => {
    expect(imagePreviewModalSource).toContain(
      "top: calc(env(safe-area-inset-top) + 170rpx);",
    );
    expect(imagePreviewModalSource).not.toContain(
      "top: calc(env(safe-area-inset-top) + 28rpx);",
    );
  });
});
