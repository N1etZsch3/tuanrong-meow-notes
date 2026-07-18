import { request } from "@/services/request";
import { API_ENDPOINTS } from "@/api/routes";
import type { AdminUserDto } from "@/api/admin-users";
import type { TitleKey, TitleShield, UserTitle } from "@/constants/titles";

export interface TitleHolder {
  user_id: string;
  meow_no: string;
  nickname: string;
}

export interface TitleCatalogItem {
  key: TitleKey;
  label: string;
  shield: TitleShield;
  is_available: boolean;
  holder: TitleHolder | null;
}

export interface TitleCatalogResponse {
  items: TitleCatalogItem[];
}

export interface TitleIdentityResponse {
  title: UserTitle;
  title_label: string | null;
  title_shield: TitleShield | null;
}

export interface PresidentTransferResponse {
  previous_president: AdminUserDto;
  successor: AdminUserDto;
}

export function getTitleCatalog(accessToken: string): Promise<TitleCatalogResponse> {
  return request<TitleCatalogResponse>({
    url: API_ENDPOINTS.admin.titles,
    method: "GET",
    token: accessToken,
  });
}

export function setMemberTitle(
  accessToken: string,
  userId: string,
  title: UserTitle,
): Promise<AdminUserDto> {
  return request<AdminUserDto, { title: UserTitle }>({
    url: API_ENDPOINTS.admin.userTitle(userId),
    method: "PATCH",
    data: { title },
    token: accessToken,
  });
}

export function transferPresident(
  accessToken: string,
  successorId: string,
): Promise<PresidentTransferResponse> {
  return request<PresidentTransferResponse, { successor_id: string }>({
    url: API_ENDPOINTS.admin.titleTransfer,
    method: "POST",
    data: { successor_id: successorId },
    token: accessToken,
  });
}

export function resignMyTitle(accessToken: string): Promise<TitleIdentityResponse> {
  return request<TitleIdentityResponse>({
    url: API_ENDPOINTS.profile.titleResign,
    method: "POST",
    token: accessToken,
  });
}
