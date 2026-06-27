from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import APIError, ErrorCode
from app.modules.files.presets import ALLOWED_MIME_TYPES, ImagePreset, VariantSpec


@dataclass(frozen=True)
class ProcessedVariant:
    variant_key: str
    body: bytes
    width: int
    height: int
    size_bytes: int
    mime_type: str
    file_ext: str
    quality: int
    resize_mode: str
    checksum_sha256: str


@dataclass(frozen=True)
class ProcessedImage:
    source_mime_type: str
    source_width: int
    source_height: int
    source_size_bytes: int
    source_checksum_sha256: str
    variants: tuple[ProcessedVariant, ...]


def process_image(
    *,
    file_bytes: bytes,
    preset: ImagePreset,
    max_pixels: int,
) -> ProcessedImage:
    if not file_bytes:
        raise APIError(code=ErrorCode.FILE_EMPTY, message="文件不能为空", status_code=400)

    try:
        with Image.open(BytesIO(file_bytes)) as probe:
            source_mime_type = Image.MIME.get(probe.format or "")
            if source_mime_type not in ALLOWED_MIME_TYPES:
                raise APIError(
                    code=ErrorCode.FILE_TYPE_UNSUPPORTED,
                    message="文件类型不支持",
                    status_code=400,
                )
            source_width, source_height = probe.size
            if source_width * source_height > max_pixels:
                raise APIError(
                    code=ErrorCode.FILE_IMAGE_TOO_LARGE,
                    message="图片尺寸超过限制",
                    status_code=400,
                )
            probe.verify()

        with Image.open(BytesIO(file_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            variants = tuple(_build_variant(image, spec) for spec in preset.variants)
    except APIError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise APIError(
            code=ErrorCode.FILE_IMAGE_INVALID,
            message="图片内容损坏或无法解析",
            status_code=400,
        ) from exc

    return ProcessedImage(
        source_mime_type=source_mime_type or "application/octet-stream",
        source_width=source_width,
        source_height=source_height,
        source_size_bytes=len(file_bytes),
        source_checksum_sha256=sha256(file_bytes).hexdigest(),
        variants=variants,
    )


def _build_variant(image: Image.Image, spec: VariantSpec) -> ProcessedVariant:
    if spec.width and spec.height:
        resized = ImageOps.fit(
            image,
            (spec.width, spec.height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    elif spec.max_edge:
        resized = image.copy()
        resized.thumbnail((spec.max_edge, spec.max_edge), Image.Resampling.LANCZOS)
    else:
        resized = image.copy()

    buffer = BytesIO()
    resized.save(buffer, format="JPEG", quality=spec.quality, optimize=True)
    body = buffer.getvalue()
    return ProcessedVariant(
        variant_key=spec.variant_key,
        body=body,
        width=resized.width,
        height=resized.height,
        size_bytes=len(body),
        mime_type="image/jpeg",
        file_ext="jpg",
        quality=spec.quality,
        resize_mode=spec.resize_mode,
        checksum_sha256=sha256(body).hexdigest(),
    )
