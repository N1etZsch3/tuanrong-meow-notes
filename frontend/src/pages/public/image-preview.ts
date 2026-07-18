import { resolvePublicImage } from "./public-assets";

export function previewPublicImage(
  currentUrl: string | null | undefined,
  imageUrls: Array<string | null | undefined>,
): void {
  const urls = Array.from(
    new Set(imageUrls.map((url) => resolvePublicImage(url)).filter(Boolean)),
  );
  const requestedCurrent = resolvePublicImage(currentUrl);

  if (!urls.length) {
    return;
  }

  const current = urls.includes(requestedCurrent) ? requestedCurrent : urls[0];
  uni.previewImage({
    current,
    urls,
  });
}
