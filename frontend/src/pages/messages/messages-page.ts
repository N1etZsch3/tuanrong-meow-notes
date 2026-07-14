/**
 * 喵息（消息通知）页面的纯逻辑层。
 *
 * 约定：本模块不依赖 uni.* / Vue 响应式 / 网络，只做数据映射、排序、
 * 过滤与状态归约，便于单元测试。页面与 WebSocket 通道负责副作用。
 *
 * `notification_type` 取值对齐后端《用户与个人中心模块》通知表设计文档 §5.4，
 * 其中 `medicine_updated` 为客户端 mock 阶段的前瞻扩展（v1 枚举未含药品提醒），
 * 后端落地后在此集中调整映射即可。
 */

/** 列表页与详情页共用的本地标记存储键（mock 阶段）。 */
export const MESSAGES_LOCAL_STATE_STORAGE_KEY = "cat_map_messages_local_state_v1";

/**
 * 列表页跳转详情前写入的消息快照键：实时推送的消息不在静态 mock
 * 数据里，详情页优先读取快照，再回退到 mock 数据查找。
 */
export const MESSAGES_DETAIL_SNAPSHOT_STORAGE_KEY = "cat_map_messages_detail_snapshot_v1";

export type NotificationType =
  | "new_task"
  | "emergency_task"
  | "task_joined"
  | "task_assigned"
  | "assignment_accepted"
  | "assignment_rejected"
  | "task_full"
  | "task_abandoned"
  | "task_checkin"
  | "review_approved"
  | "review_rejected"
  | "cat_health_abnormal"
  | "supply_updated"
  | "medicine_updated"
  | "announcement";

export type NotificationRelatedType =
  | "task"
  | "cat"
  | "supply_point"
  | "medicine"
  | "announcement"
  | "map_point";

/** 后端返回的通知条目（snake_case，镜像通知表）。 */
export interface NotificationItemDto {
  id: string;
  notification_type: NotificationType;
  title: string;
  content: string;
  related_type: NotificationRelatedType | null;
  related_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

/**
 * 客户端本地三态标记。后端通知表暂不含置顶/标签/免打扰/完成字段，
 * 这些为端上体验，落库前持久化在本地存储，后端补齐后可平滑迁移。
 */
export interface NotificationLocalState {
  is_pinned: boolean;
  is_muted: boolean;
  is_dismissed: boolean;
  label_key: NotificationLabelKey | null;
}

/** 合并后端条目与本地标记的视图模型。 */
export interface NotificationView extends NotificationItemDto, NotificationLocalState {}

export type MessagesTabKey = "all" | "unread";

/** 展示频道：决定头像、强调色与来源徽标。 */
export type NotificationChannelKey =
  | "task"
  | "feeding"
  | "medicine"
  | "supply"
  | "member"
  | "cat"
  | "announcement";

export type NotificationTone = "green" | "amber" | "violet" | "sky" | "rose" | "leaf";

export interface NotificationChannel {
  key: NotificationChannelKey;
  /** 卡片主标题（频道名）。 */
  title: string;
  /** 来源徽标文案：官方 / 系统 / 管理 / 提醒。 */
  badge: string;
  tone: NotificationTone;
  /** 头像图标键，页面据此选择素材。 */
  icon_key: NotificationChannelKey;
}

export const NOTIFICATION_CHANNELS: Record<NotificationChannelKey, NotificationChannel> = {
  task: { key: "task", title: "任务系统", badge: "官方", tone: "green", icon_key: "task" },
  feeding: { key: "feeding", title: "喂食提醒", badge: "系统", tone: "amber", icon_key: "feeding" },
  medicine: { key: "medicine", title: "药品管理", badge: "管理", tone: "violet", icon_key: "medicine" },
  supply: { key: "supply", title: "物资通知", badge: "系统", tone: "leaf", icon_key: "supply" },
  member: { key: "member", title: "成员通知", badge: "官方", tone: "sky", icon_key: "member" },
  cat: { key: "cat", title: "猫咪健康", badge: "提醒", tone: "rose", icon_key: "cat" },
  announcement: { key: "announcement", title: "系统公告", badge: "官方", tone: "sky", icon_key: "announcement" },
};

const TYPE_TO_CHANNEL: Record<NotificationType, NotificationChannelKey> = {
  new_task: "task",
  emergency_task: "task",
  task_joined: "task",
  task_assigned: "task",
  assignment_accepted: "task",
  assignment_rejected: "task",
  task_full: "task",
  task_abandoned: "task",
  task_checkin: "feeding",
  review_approved: "member",
  review_rejected: "member",
  cat_health_abnormal: "cat",
  supply_updated: "supply",
  medicine_updated: "medicine",
  announcement: "announcement",
};

export function resolveNotificationChannel(type: NotificationType): NotificationChannel {
  return NOTIFICATION_CHANNELS[TYPE_TO_CHANNEL[type] ?? "announcement"];
}

/** 可选颜色标签（“标签”操作）。 */
export type NotificationLabelKey = "important" | "follow_up" | "resolved";

export interface NotificationLabel {
  key: NotificationLabelKey;
  text: string;
  tone: NotificationTone;
}

export const NOTIFICATION_LABELS: Record<NotificationLabelKey, NotificationLabel> = {
  important: { key: "important", text: "重要", tone: "rose" },
  follow_up: { key: "follow_up", text: "待跟进", tone: "amber" },
  resolved: { key: "resolved", text: "已处理", tone: "green" },
};

export const NOTIFICATION_LABEL_ORDER: NotificationLabelKey[] = [
  "important",
  "follow_up",
  "resolved",
];

export function getNotificationLabel(
  key: NotificationLabelKey | null,
): NotificationLabel | null {
  return key ? NOTIFICATION_LABELS[key] : null;
}

export function createDefaultLocalState(): NotificationLocalState {
  return {
    is_pinned: false,
    is_muted: false,
    is_dismissed: false,
    label_key: null,
  };
}

/**
 * 将后端条目与本地标记合并为视图模型；缺失的本地标记以默认值补齐。
 */
export function toNotificationView(
  dto: NotificationItemDto,
  local?: Partial<NotificationLocalState> | null,
): NotificationView {
  return {
    ...dto,
    ...createDefaultLocalState(),
    ...(local ?? {}),
  };
}

/**
 * 合并增量推送：按 id 去重，新数据覆盖旧数据但保留既有本地标记，
 * 未 dismiss 的条目才纳入。返回排序前的列表。
 */
export function mergeIncomingNotifications(
  current: NotificationView[],
  incoming: NotificationItemDto[],
): NotificationView[] {
  const byId = new Map<string, NotificationView>();
  for (const item of current) {
    byId.set(item.id, item);
  }
  for (const dto of incoming) {
    const existing = byId.get(dto.id);
    if (existing) {
      byId.set(dto.id, {
        ...existing,
        ...dto,
        is_pinned: existing.is_pinned,
        is_muted: existing.is_muted,
        is_dismissed: existing.is_dismissed,
        label_key: existing.label_key,
      });
    } else {
      byId.set(dto.id, toNotificationView(dto));
    }
  }
  return [...byId.values()];
}

function toTimestamp(iso: string): number {
  const value = new Date(iso).getTime();
  return Number.isNaN(value) ? 0 : value;
}

/** 排序：置顶优先，其次按创建时间倒序。 */
export function sortNotifications(items: NotificationView[]): NotificationView[] {
  return [...items].sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) {
      return a.is_pinned ? -1 : 1;
    }
    return toTimestamp(b.created_at) - toTimestamp(a.created_at);
  });
}

/** 过滤：始终排除已完成（dismissed）；未读页仅保留未读。 */
export function filterNotifications(
  items: NotificationView[],
  tab: MessagesTabKey,
): NotificationView[] {
  const visible = items.filter((item) => !item.is_dismissed);
  if (tab === "unread") {
    return visible.filter((item) => !item.is_read);
  }
  return visible;
}

export function selectNotifications(
  items: NotificationView[],
  tab: MessagesTabKey,
): NotificationView[] {
  return sortNotifications(filterNotifications(items, tab));
}

/** 未读计数（排除已完成）。 */
export function countUnread(items: NotificationView[]): number {
  return items.filter((item) => !item.is_dismissed && !item.is_read).length;
}

// ---- 状态归约（纯函数，返回新数组） ----

function patchById(
  items: NotificationView[],
  id: string,
  patch: Partial<NotificationView>,
): NotificationView[] {
  return items.map((item) => (item.id === id ? { ...item, ...patch } : item));
}

export function markRead(items: NotificationView[], id: string): NotificationView[] {
  return items.map((item) =>
    item.id === id && !item.is_read
      ? { ...item, is_read: true, read_at: item.read_at ?? new Date().toISOString() }
      : item,
  );
}

export function markUnread(items: NotificationView[], id: string): NotificationView[] {
  return patchById(items, id, { is_read: false, read_at: null });
}

export function togglePinned(items: NotificationView[], id: string): NotificationView[] {
  const target = items.find((item) => item.id === id);
  return patchById(items, id, { is_pinned: !(target?.is_pinned ?? false) });
}

export function toggleMuted(items: NotificationView[], id: string): NotificationView[] {
  const target = items.find((item) => item.id === id);
  return patchById(items, id, { is_muted: !(target?.is_muted ?? false) });
}

export function setLabel(
  items: NotificationView[],
  id: string,
  labelKey: NotificationLabelKey | null,
): NotificationView[] {
  const target = items.find((item) => item.id === id);
  // 再次点选同一标签则取消。
  const next = target?.label_key === labelKey ? null : labelKey;
  return patchById(items, id, { label_key: next });
}

/** 完成：标记 dismissed 并置为已读，列表中不再展示。 */
export function dismissNotification(items: NotificationView[], id: string): NotificationView[] {
  return items.map((item) =>
    item.id === id
      ? {
          ...item,
          is_dismissed: true,
          is_read: true,
          read_at: item.read_at ?? new Date().toISOString(),
        }
      : item,
  );
}

/** 将所有未完成的未读消息标记为已读，消息记录仍保留。 */
export function markAllRead(items: NotificationView[]): NotificationView[] {
  const now = new Date().toISOString();
  return items.map((item) =>
    item.is_dismissed || item.is_read
      ? item
      : { ...item, is_read: true, read_at: now },
  );
}

/**
 * 提取需持久化的本地标记（仅存偏离默认值的条目，控制存储体积）。
 */
export interface StoredLocalState extends NotificationLocalState {
  id: string;
}

export function extractLocalStates(items: NotificationView[]): StoredLocalState[] {
  const result: StoredLocalState[] = [];
  for (const item of items) {
    const isDefault =
      !item.is_pinned && !item.is_muted && !item.is_dismissed && item.label_key === null;
    if (!isDefault) {
      result.push({
        id: item.id,
        is_pinned: item.is_pinned,
        is_muted: item.is_muted,
        is_dismissed: item.is_dismissed,
        label_key: item.label_key,
      });
    }
  }
  return result;
}

export function indexLocalStates(
  stored: StoredLocalState[] | null | undefined,
): Record<string, NotificationLocalState> {
  const index: Record<string, NotificationLocalState> = {};
  if (!stored) {
    return index;
  }
  for (const entry of stored) {
    index[entry.id] = {
      is_pinned: Boolean(entry.is_pinned),
      is_muted: Boolean(entry.is_muted),
      is_dismissed: Boolean(entry.is_dismissed),
      label_key: entry.label_key ?? null,
    };
  }
  return index;
}

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;

function pad(value: number): string {
  return value < 10 ? `0${value}` : `${value}`;
}

/**
 * 相对时间：刚刚 / N分钟前 / 今天 HH:mm / 昨天 / M月D日 / YYYY/M/D。
 * `now` 可注入以便测试。
 */
export function formatNotificationTime(iso: string, now: number = Date.now()): string {
  const then = toTimestamp(iso);
  if (!then) {
    return "";
  }
  const diff = now - then;
  if (diff < MINUTE) {
    return "刚刚";
  }
  if (diff < HOUR) {
    return `${Math.floor(diff / MINUTE)}分钟前`;
  }

  const thenDate = new Date(then);
  const nowDate = new Date(now);
  const sameDay =
    thenDate.getFullYear() === nowDate.getFullYear() &&
    thenDate.getMonth() === nowDate.getMonth() &&
    thenDate.getDate() === nowDate.getDate();
  if (sameDay) {
    return `今天 ${pad(thenDate.getHours())}:${pad(thenDate.getMinutes())}`;
  }

  const yesterday = new Date(now - 24 * HOUR);
  const isYesterday =
    thenDate.getFullYear() === yesterday.getFullYear() &&
    thenDate.getMonth() === yesterday.getMonth() &&
    thenDate.getDate() === yesterday.getDate();
  if (isYesterday) {
    return "昨天";
  }

  if (thenDate.getFullYear() === nowDate.getFullYear()) {
    return `${thenDate.getMonth() + 1}月${thenDate.getDate()}日`;
  }
  return `${thenDate.getFullYear()}/${thenDate.getMonth() + 1}/${thenDate.getDate()}`;
}
