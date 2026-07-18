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
  tag_background: string;
  tag_color: string;
}

export const TITLE_DEFINITIONS: readonly TitleDefinition[] = [
  { key: "president", label: "会长", shield: "gold", tag_background: "#fff0bd", tag_color: "#7b5200" },
  { key: "vice_president", label: "副会长", shield: "purple", tag_background: "#eee3ff", tag_color: "#6840a8" },
  { key: "survival_head", label: "生存保障部部长", shield: "green", tag_background: "#dff3df", tag_color: "#286f32" },
  { key: "survival_deputy", label: "生存保障部副部长", shield: "green", tag_background: "#e5f4d8", tag_color: "#43742d" },
  { key: "activity_head", label: "活动部部长", shield: "green", tag_background: "#d9f0e7", tag_color: "#23705d" },
  { key: "activity_deputy", label: "活动部副部长", shield: "green", tag_background: "#e1f2ee", tag_color: "#356d62" },
  { key: "publicity_head", label: "宣传部部长", shield: "green", tag_background: "#dceee3", tag_color: "#2e6b47" },
  { key: "publicity_deputy", label: "宣传部副部长", shield: "green", tag_background: "#e9f2d8", tag_color: "#526f2f" },
  { key: "secretary_head", label: "秘书部部长", shield: "green", tag_background: "#d8f0dc", tag_color: "#28693a" },
  { key: "secretary_deputy", label: "秘书部副部长", shield: "green", tag_background: "#e4efcf", tag_color: "#5b6d2e" },
  { key: "care_head", label: "养护部部长", shield: "green", tag_background: "#d7eee9", tag_color: "#246b5f" },
  { key: "care_deputy", label: "养护部副部长", shield: "green", tag_background: "#e7f0dd", tag_color: "#476d3c" },
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
