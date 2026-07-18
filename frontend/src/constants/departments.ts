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

type DepartmentTagColors = {
  background: string;
  text: string;
};

const DEPARTMENT_TAG_COLORS: Record<Department, DepartmentTagColors> = {
  生存保障部: { background: "#dff4e4", text: "#2f7545" },
  活动部: { background: "#fff0d6", text: "#9a5d16" },
  宣传部: { background: "#eee6ff", text: "#6c4a9c" },
  秘书部: { background: "#fbe5ec", text: "#95536a" },
  养护部: { background: "#deeff8", text: "#346f8a" },
};

const UNKNOWN_DEPARTMENT_TAG_COLORS: DepartmentTagColors = {
  background: "#edf0f3",
  text: "#526070",
};

export function isKnownDepartment(value: string): value is Department {
  return (DEPARTMENTS as readonly string[]).includes(value);
}

export function getDepartmentTagColors(department: string): DepartmentTagColors {
  return isKnownDepartment(department)
    ? DEPARTMENT_TAG_COLORS[department]
    : UNKNOWN_DEPARTMENT_TAG_COLORS;
}

export function getDepartmentTagStyle(department: string): Record<string, string> {
  const colors = getDepartmentTagColors(department);
  return {
    backgroundColor: colors.background,
    color: colors.text,
  };
}
