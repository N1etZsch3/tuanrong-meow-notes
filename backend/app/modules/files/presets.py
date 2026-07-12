from dataclasses import dataclass


@dataclass(frozen=True)
class VariantSpec:
    variant_key: str
    max_edge: int | None = None
    width: int | None = None
    height: int | None = None
    resize_mode: str = "fit"
    quality: int = 82


@dataclass(frozen=True)
class ImagePreset:
    preset_key: str
    variants: tuple[VariantSpec, ...]
    default_variant_key: str
    default_thumb_variant_key: str


@dataclass(frozen=True)
class UsageTypeConfig:
    usage_type: str
    label: str
    process_preset: str
    max_file_size_bytes: int
    max_batch_count: int
    allowed_roles: tuple[str, ...] = ("member", "summer_volunteer", "admin", "super_admin")


DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_BATCH_COUNT = 9
DEFAULT_MAX_PIXELS = 20_000_000
ALLOWED_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "webp")


IMAGE_PRESETS: dict[str, ImagePreset] = {
    "avatar_v1": ImagePreset(
        preset_key="avatar_v1",
        variants=(
            VariantSpec("avatar_sm", width=128, height=128, resize_mode="cover", quality=82),
            VariantSpec("avatar_md", width=256, height=256, resize_mode="cover", quality=82),
            VariantSpec("avatar_lg", width=512, height=512, resize_mode="cover", quality=85),
        ),
        default_variant_key="avatar_lg",
        default_thumb_variant_key="avatar_md",
    ),
    "normal_photo_v1": ImagePreset(
        preset_key="normal_photo_v1",
        variants=(
            VariantSpec("thumb_sm", max_edge=160, quality=78),
            VariantSpec("thumb_md", max_edge=320, quality=80),
            VariantSpec("preview_lg", max_edge=720, quality=82),
            VariantSpec("display", max_edge=1280, quality=82),
        ),
        default_variant_key="display",
        default_thumb_variant_key="thumb_md",
    ),
    "route_photo_v1": ImagePreset(
        preset_key="route_photo_v1",
        variants=(
            VariantSpec("thumb_md", max_edge=320, quality=80),
            VariantSpec("preview_lg", max_edge=720, quality=82),
            VariantSpec("route_display", max_edge=1600, quality=85),
        ),
        default_variant_key="route_display",
        default_thumb_variant_key="thumb_md",
    ),
    "high_detail_photo_v1": ImagePreset(
        preset_key="high_detail_photo_v1",
        variants=(
            VariantSpec("thumb_md", max_edge=320, quality=80),
            VariantSpec("preview_lg", max_edge=720, quality=83),
            VariantSpec("display", max_edge=1600, quality=85),
        ),
        default_variant_key="display",
        default_thumb_variant_key="thumb_md",
    ),
}


USAGE_TYPE_CONFIGS: dict[str, UsageTypeConfig] = {
    "user_avatar": UsageTypeConfig(
        "user_avatar",
        "用户头像",
        "avatar_v1",
        5 * 1024 * 1024,
        1,
    ),
    "cat_avatar": UsageTypeConfig(
        "cat_avatar",
        "猫咪头像",
        "avatar_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        1,
        allowed_roles=("admin", "super_admin"),
    ),
    "cat_photo": UsageTypeConfig(
        "cat_photo",
        "猫咪照片",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
    ),
    "cat_health_photo": UsageTypeConfig(
        "cat_health_photo",
        "猫咪健康照片",
        "high_detail_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
    ),
    "map_point_cover": UsageTypeConfig(
        "map_point_cover",
        "点位封面图",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        1,
        allowed_roles=("admin", "super_admin"),
    ),
    "map_point_scene": UsageTypeConfig(
        "map_point_scene",
        "点位现场图",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
        allowed_roles=("admin", "super_admin"),
    ),
    "map_point_route": UsageTypeConfig(
        "map_point_route",
        "点位路线图",
        "route_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        6,
        allowed_roles=("admin", "super_admin"),
    ),
    "task_checkin_photo": UsageTypeConfig(
        "task_checkin_photo",
        "任务打卡照片",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
    ),
    "supply_record_photo": UsageTypeConfig(
        "supply_record_photo",
        "物资记录照片",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
    ),
    "medicine_photo": UsageTypeConfig(
        "medicine_photo",
        "药品照片",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        5,
    ),
    "observation_photo": UsageTypeConfig(
        "observation_photo",
        "观察记录照片",
        "normal_photo_v1",
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_BATCH_COUNT,
    ),
}


CONTENT_SECURITY_SCENES: dict[str, int] = {
    "user_avatar": 1,
    "cat_avatar": 1,
    "cat_photo": 1,
    "cat_health_photo": 1,
    "map_point_cover": 4,
    "map_point_scene": 4,
    "map_point_route": 4,
    "task_checkin_photo": 4,
    "supply_record_photo": 4,
    "medicine_photo": 1,
    "observation_photo": 4,
}


SCENE_VARIANT_MAP: dict[str, str] = {
    "avatar_in_list": "avatar_sm",
    "avatar_profile": "avatar_lg",
    "cat_list_cover": "thumb_md",
    "cat_detail_preview": "preview_lg",
    "cat_detail_full": "display",
    "map_marker_preview": "thumb_sm",
    "map_bottom_card": "thumb_md",
    "map_point_detail": "display",
    "route_photo_detail": "route_display",
    "health_photo_detail": "display",
    "task_list_cover": "thumb_md",
    "task_detail_full": "display",
    "task_checkin_list": "thumb_md",
    "task_checkin_detail": "display",
    "supply_record_list": "thumb_md",
    "supply_record_detail": "display",
}


def upload_config_payload() -> dict:
    return {
        "max_file_size_bytes": DEFAULT_MAX_FILE_SIZE_BYTES,
        "max_batch_count": DEFAULT_MAX_BATCH_COUNT,
        "allowed_mime_types": list(ALLOWED_MIME_TYPES),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "usage_types": [
            {
                "usage_type": config.usage_type,
                "label": config.label,
                "process_preset": config.process_preset,
                "max_file_size_bytes": config.max_file_size_bytes,
                "max_batch_count": config.max_batch_count,
                "variants": [
                    variant.variant_key for variant in IMAGE_PRESETS[config.process_preset].variants
                ],
            }
            for config in USAGE_TYPE_CONFIGS.values()
        ],
    }
