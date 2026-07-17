"""头衔（title）注册表：13 个头衔的键、文案、盾牌配色分组。

前端 constants/titles.ts 与此保持一致。存储层：user_profiles.title 存
头衔 key；NULL 表示无头衔（none）。除 none 外 12 个头衔全局唯一。
"""

PRESIDENT = "president"
VICE_PRESIDENT = "vice_president"
NONE_TITLE = "none"

# 5 部门键（与 profile 部门文案对应）
DEPARTMENT_TITLE_PREFIXES = {
    "survival": "生存保障部",
    "activity": "活动部",
    "publicity": "宣传部",
    "secretary": "秘书部",
    "care": "养护部",
}

# 头衔 key -> 中文标签
TITLE_LABELS: dict[str, str] = {
    PRESIDENT: "会长",
    VICE_PRESIDENT: "副会长",
}
for _key, _dept in DEPARTMENT_TITLE_PREFIXES.items():
    TITLE_LABELS[f"{_key}_head"] = f"{_dept}部长"
    TITLE_LABELS[f"{_key}_deputy"] = f"{_dept}副部长"

# 全部合法头衔键（含 none）
ALL_TITLE_KEYS: tuple[str, ...] = (NONE_TITLE, *TITLE_LABELS.keys())
# 除 none 外的头衔（全局唯一）
UNIQUE_TITLE_KEYS: tuple[str, ...] = tuple(TITLE_LABELS.keys())

# 盾牌配色分组：会长金 / 副会长紫 / 其余部长副部长绿
SHIELD_GOLD = "gold"
SHIELD_PURPLE = "purple"
SHIELD_GREEN = "green"


def shield_variant(title: str | None) -> str | None:
    if title == PRESIDENT:
        return SHIELD_GOLD
    if title == VICE_PRESIDENT:
        return SHIELD_PURPLE
    if title in TITLE_LABELS:
        return SHIELD_GREEN
    return None


def normalize_title(title: str | None) -> str | None:
    """把 none/空串统一成 None（无头衔）。"""
    if not title or title == NONE_TITLE:
        return None
    return title


def is_valid_title(title: str | None) -> bool:
    return title is None or title in ALL_TITLE_KEYS


def title_label(title: str | None) -> str | None:
    normalized = normalize_title(title)
    return TITLE_LABELS.get(normalized) if normalized else None


def title_payload(title: str | None) -> dict[str, str | None]:
    normalized = normalize_title(title)
    return {
        "title": normalized,
        "title_label": title_label(normalized),
        "title_shield": shield_variant(normalized),
    }
