import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";
import type { NotificationItemDto } from "@/pages/messages/messages-page";

export interface NotificationListQuery {
  is_read?: boolean;
  notification_type?: string;
  page?: number;
  page_size?: number;
}

export interface NotificationListResponse {
  items: NotificationItemDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface NotificationSettingsDto {
  task_enabled: boolean;
  feeding_enabled: boolean;
  medicine_enabled: boolean;
  supply_enabled: boolean;
  member_enabled: boolean;
  cat_enabled: boolean;
  announcement_enabled: boolean;
}

export function getNotifications(
  accessToken: string,
  query: NotificationListQuery = {},
): Promise<NotificationListResponse> {
  return request<NotificationListResponse>({
    url: API_ENDPOINTS.me.notifications,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getNotificationUnreadCount(
  accessToken: string,
): Promise<{ unread_count: number }> {
  return request<{ unread_count: number }>({
    url: API_ENDPOINTS.me.notificationUnreadCount,
    method: "GET",
    token: accessToken,
  });
}

export function markNotificationRead(
  accessToken: string,
  notificationId: string,
): Promise<{ id: string; is_read: boolean; read_at: string | null }> {
  return request<{ id: string; is_read: boolean; read_at: string | null }>({
    url: API_ENDPOINTS.me.notificationRead(notificationId),
    method: "PATCH",
    token: accessToken,
  });
}

export function markAllNotificationsRead(
  accessToken: string,
): Promise<{ updated_count: number }> {
  return request<{ updated_count: number }>({
    url: API_ENDPOINTS.me.notificationReadAll,
    method: "PATCH",
    token: accessToken,
  });
}

export function getNotificationSettings(
  accessToken: string,
): Promise<NotificationSettingsDto> {
  return request<NotificationSettingsDto>({
    url: API_ENDPOINTS.me.notificationSettings,
    method: "GET",
    token: accessToken,
  });
}

export function updateNotificationSettings(
  accessToken: string,
  changes: Partial<NotificationSettingsDto>,
): Promise<NotificationSettingsDto> {
  return request<NotificationSettingsDto, Partial<NotificationSettingsDto> & Record<string, unknown>>({
    url: API_ENDPOINTS.me.notificationSettings,
    method: "PATCH",
    data: { ...changes },
    token: accessToken,
  });
}
