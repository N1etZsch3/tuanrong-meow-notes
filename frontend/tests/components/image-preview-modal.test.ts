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

  it("uses a native swiper so pages follow the finger while dragging", () => {
    expect(imagePreviewModalSource).toContain("<swiper");
    expect(imagePreviewModalSource).toContain("<swiper-item");
    expect(imagePreviewModalSource).toContain(':current="activeIndex"');
    expect(imagePreviewModalSource).toContain('@change="handleSwiperChange"');
    expect(imagePreviewModalSource).toContain("emit(\"change\"");
    expect(imagePreviewModalSource).not.toContain("uni.previewImage");
    expect(imagePreviewModalSource).not.toContain("handlePreviewTouchEnd");
    expect(imagePreviewModalSource).not.toContain("SWIPE_MIN_DISTANCE");
  });

  it("closes when tapping anywhere on the screen, including the image", () => {
    expect(imagePreviewModalSource).toContain('@tap="close"');
    expect(imagePreviewModalSource).toContain("emit(\"close\")");
    expect(imagePreviewModalSource).toMatch(
      /<image[^>]*@tap="close"|@tap="close"[^>]*>[\s\S]*?<image/,
    );
    expect(imagePreviewModalSource).not.toContain("@tap.stop");
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
