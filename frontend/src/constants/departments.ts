// 猫协 5 个固定部门的共享常量（收敛此前分散在 5 个页面的重复硬编码）。
// 后端权威定义为 profile/schemas.py 的 Department Literal，此处与之保持一致。

export const DEPARTMENTS = [
  "生存保障部",
  "活动部",
  "宣传部",
  "秘书部",
  "养护部",
] as const;

export type Department = (typeof DEPARTMENTS)[number];

export type DepartmentThemeColors = {
  background: string;
  text: string;
  head_title: string;
  deputy_title: string;
};

export const DEPARTMENT_THEMES: Record<Department, DepartmentThemeColors> = {
  生存保障部: {
    background: "#e7f1d9",
    text: "#4d722c",
    head_title: "#4d722c",
    deputy_title: "#66745a",
  },
  活动部: {
    background: "#fbe5da",
    text: "#b74b1f",
    head_title: "#b74b1f",
    deputy_title: "#876b5f",
  },
  宣传部: {
    background: "#f4dfed",
    text: "#963b7a",
    head_title: "#963b7a",
    deputy_title: "#7f6778",
  },
  秘书部: {
    background: "#dfe9f2",
    text: "#365a7a",
    head_title: "#365a7a",
    deputy_title: "#657482",
  },
  养护部: {
    background: "#ddf0ec",
    text: "#24786c",
    head_title: "#24786c",
    deputy_title: "#607c77",
  },
};

const UNKNOWN_DEPARTMENT_TAG_COLORS: DepartmentThemeColors = {
  background: "#edf0f3",
  text: "#526070",
  head_title: "#526070",
  deputy_title: "#6f7780",
};

export function isKnownDepartment(value: string): value is Department {
  return (DEPARTMENTS as readonly string[]).includes(value);
}

export function getDepartmentThemeColors(department: string): DepartmentThemeColors {
  return isKnownDepartment(department)
    ? DEPARTMENT_THEMES[department]
    : UNKNOWN_DEPARTMENT_TAG_COLORS;
}

export function getDepartmentTagColors(
  department: string,
): Pick<DepartmentThemeColors, "background" | "text"> {
  const colors = getDepartmentThemeColors(department);
  return { background: colors.background, text: colors.text };
}

export function getDepartmentTagStyle(department: string): Record<string, string> {
  const colors = getDepartmentTagColors(department);
  return {
    backgroundColor: colors.background,
    color: colors.text,
  };
}
