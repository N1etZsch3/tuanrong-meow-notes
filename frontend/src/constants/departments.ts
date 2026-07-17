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

export function isKnownDepartment(value: string): value is Department {
  return (DEPARTMENTS as readonly string[]).includes(value);
}
