// The public mock content references bundled photos by a stable
// "/static/public/<name>.jpg" path. In the WeChat Mini Program a bare server path
// does not resolve, so map those known paths to imported bundle assets. When the
// backend later serves real (absolute COS) URLs, those pass through unchanged.
import cat1 from "@/static/public/cat-1.jpg";
import cat2 from "@/static/public/cat-2.jpg";
import cat3 from "@/static/public/cat-3.jpg";
import cat4 from "@/static/public/cat-4.jpg";
import cat5 from "@/static/public/cat-5.jpg";
import cat6 from "@/static/public/cat-6.jpg";

const BUNDLED_PUBLIC_IMAGES: Record<string, string> = {
  "/static/public/cat-1.jpg": cat1,
  "/static/public/cat-2.jpg": cat2,
  "/static/public/cat-3.jpg": cat3,
  "/static/public/cat-4.jpg": cat4,
  "/static/public/cat-5.jpg": cat5,
  "/static/public/cat-6.jpg": cat6,
};

export function resolvePublicImage(url: string | null | undefined): string {
  if (!url) {
    return "";
  }
  if (BUNDLED_PUBLIC_IMAGES[url]) {
    return BUNDLED_PUBLIC_IMAGES[url];
  }
  return url;
}
