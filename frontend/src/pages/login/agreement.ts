import { STORAGE_KEYS } from "@/constants/storage";

const MAX_REMEMBERED_ACCOUNTS = 50;

export function normalizeAgreementAccount(account: string | null | undefined): string {
  return String(account ?? "").trim().toLowerCase();
}

function readAcceptedAgreementAccounts(): string[] {
  const value = uni.getStorageSync(STORAGE_KEYS.agreementAcceptedAccounts);
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((account) =>
      typeof account === "string" ? normalizeAgreementAccount(account) : "",
    )
    .filter(Boolean);
}

export function hasAcceptedAgreementForAccount(account: string | null | undefined): boolean {
  const normalizedAccount = normalizeAgreementAccount(account);
  if (!normalizedAccount) {
    return false;
  }

  return readAcceptedAgreementAccounts().includes(normalizedAccount);
}

export function rememberAgreementAcceptedForAccounts(
  accounts: Array<string | null | undefined>,
): void {
  const rememberedAccounts = readAcceptedAgreementAccounts();
  const nextAccounts = [
    ...accounts.map(normalizeAgreementAccount).filter(Boolean),
    ...rememberedAccounts,
  ];
  const uniqueAccounts = Array.from(new Set(nextAccounts)).slice(
    0,
    MAX_REMEMBERED_ACCOUNTS,
  );

  uni.setStorageSync(STORAGE_KEYS.agreementAcceptedAccounts, uniqueAccounts);
}
