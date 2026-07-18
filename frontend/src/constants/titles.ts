import { DEPARTMENT_THEMES } from "@/constants/departments";

export type TitleKey =
  | "president"
  | "vice_president"
  | "survival_head"
  | "survival_deputy"
  | "activity_head"
  | "activity_deputy"
  | "publicity_head"
  | "publicity_deputy"
  | "secretary_head"
  | "secretary_deputy"
  | "care_head"
  | "care_deputy";

export type UserTitle = TitleKey | null;
export type TitleShield = "gold" | "purple" | "green";

export interface TitleDefinition {
  key: TitleKey;
  label: string;
  shield: TitleShield;
  shield_asset: TitleKey;
  tag_background: string;
  tag_color: string;
  name_color: string;
  rank: "president" | "vice_president" | "head" | "deputy";
}

export const TITLE_DEFINITIONS: readonly TitleDefinition[] = [
  {
    key: "president",
    label: "会长",
    shield: "gold",
    shield_asset: "president",
    tag_background: "#f8dede",
    tag_color: "#a52828",
    name_color: "#a52828",
    rank: "president",
  },
  {
    key: "vice_president",
    label: "副会长",
    shield: "purple",
    shield_asset: "vice_president",
    tag_background: "#f3e9ce",
    tag_color: "#8a6817",
    name_color: "#8a6817",
    rank: "vice_president",
  },
  {
    key: "survival_head",
    label: "生存保障部部长",
    shield: "green",
    shield_asset: "survival_head",
    tag_background: DEPARTMENT_THEMES.生存保障部.background,
    tag_color: DEPARTMENT_THEMES.生存保障部.head_title,
    name_color: DEPARTMENT_THEMES.生存保障部.head_title,
    rank: "head",
  },
  {
    key: "survival_deputy",
    label: "生存保障部副部长",
    shield: "green",
    shield_asset: "survival_deputy",
    tag_background: DEPARTMENT_THEMES.生存保障部.background,
    tag_color: DEPARTMENT_THEMES.生存保障部.deputy_title,
    name_color: DEPARTMENT_THEMES.生存保障部.deputy_title,
    rank: "deputy",
  },
  {
    key: "activity_head",
    label: "活动部部长",
    shield: "green",
    shield_asset: "activity_head",
    tag_background: DEPARTMENT_THEMES.活动部.background,
    tag_color: DEPARTMENT_THEMES.活动部.head_title,
    name_color: DEPARTMENT_THEMES.活动部.head_title,
    rank: "head",
  },
  {
    key: "activity_deputy",
    label: "活动部副部长",
    shield: "green",
    shield_asset: "activity_deputy",
    tag_background: DEPARTMENT_THEMES.活动部.background,
    tag_color: DEPARTMENT_THEMES.活动部.deputy_title,
    name_color: DEPARTMENT_THEMES.活动部.deputy_title,
    rank: "deputy",
  },
  {
    key: "publicity_head",
    label: "宣传部部长",
    shield: "green",
    shield_asset: "publicity_head",
    tag_background: DEPARTMENT_THEMES.宣传部.background,
    tag_color: DEPARTMENT_THEMES.宣传部.head_title,
    name_color: DEPARTMENT_THEMES.宣传部.head_title,
    rank: "head",
  },
  {
    key: "publicity_deputy",
    label: "宣传部副部长",
    shield: "green",
    shield_asset: "publicity_deputy",
    tag_background: DEPARTMENT_THEMES.宣传部.background,
    tag_color: DEPARTMENT_THEMES.宣传部.deputy_title,
    name_color: DEPARTMENT_THEMES.宣传部.deputy_title,
    rank: "deputy",
  },
  {
    key: "secretary_head",
    label: "秘书部部长",
    shield: "green",
    shield_asset: "secretary_head",
    tag_background: DEPARTMENT_THEMES.秘书部.background,
    tag_color: DEPARTMENT_THEMES.秘书部.head_title,
    name_color: DEPARTMENT_THEMES.秘书部.head_title,
    rank: "head",
  },
  {
    key: "secretary_deputy",
    label: "秘书部副部长",
    shield: "green",
    shield_asset: "secretary_deputy",
    tag_background: DEPARTMENT_THEMES.秘书部.background,
    tag_color: DEPARTMENT_THEMES.秘书部.deputy_title,
    name_color: DEPARTMENT_THEMES.秘书部.deputy_title,
    rank: "deputy",
  },
  {
    key: "care_head",
    label: "养护部部长",
    shield: "green",
    shield_asset: "care_head",
    tag_background: DEPARTMENT_THEMES.养护部.background,
    tag_color: DEPARTMENT_THEMES.养护部.head_title,
    name_color: DEPARTMENT_THEMES.养护部.head_title,
    rank: "head",
  },
  {
    key: "care_deputy",
    label: "养护部副部长",
    shield: "green",
    shield_asset: "care_deputy",
    tag_background: DEPARTMENT_THEMES.养护部.background,
    tag_color: DEPARTMENT_THEMES.养护部.deputy_title,
    name_color: DEPARTMENT_THEMES.养护部.deputy_title,
    rank: "deputy",
  },
] as const;

const TITLE_BY_KEY = new Map<TitleKey, TitleDefinition>(
  TITLE_DEFINITIONS.map((definition) => [definition.key, definition]),
);

export function normalizeTitle(title: string | null | undefined): UserTitle {
  if (!title || title === "none" || !TITLE_BY_KEY.has(title as TitleKey)) {
    return null;
  }
  return title as TitleKey;
}

export function getTitleDefinition(
  title: string | null | undefined,
): TitleDefinition | null {
  const normalized = normalizeTitle(title);
  return normalized ? TITLE_BY_KEY.get(normalized) || null : null;
}
