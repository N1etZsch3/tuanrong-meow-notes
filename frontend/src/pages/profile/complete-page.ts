export function normalizeInitialProfileText(value: string | null | undefined): string {
  const text = value ?? "";
  const trimmed = text.trim();
  return trimmed && /^\?+$/.test(trimmed) ? "" : text;
}
