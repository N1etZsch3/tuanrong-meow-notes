/**
 * 喵息页面 mock 数据。
 *
 * 后端通知模块（《用户与个人中心模块》§8 通知中心接口 + notifications 表）
 * 目前仅有 dashboard 里的空桩，尚未实现。此文件提供符合该契约的样例数据，
 * 供前端页面与 mock WebSocket 通道在本地演示。后端落地后删除本文件、
 * 改为调用 getNotifications / connectNotificationSocket 真实实现即可。
 *
 * 说明：为使相对时间稳定，时间戳基于一个固定基准（BASE_TIME）向前回溯，
 * 而非 Date.now()，避免每次运行漂移，也避免在 vitest 中触发 Date 限制。
 */

import type { NotificationItemDto } from "./messages-page";

/** 固定基准：2026-07-13 09:12（+08:00），mock 展示用。 */
const BASE_TIME = new Date("2026-07-13T09:12:00+08:00").getTime();
const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

function ago(ms: number): string {
  return new Date(BASE_TIME - ms).toISOString();
}

export const MOCK_NOTIFICATIONS: NotificationItemDto[] = [
  {
    id: "ntf-1001",
    notification_type: "new_task",
    title: "新任务已发布",
    content: "白敬亭喂食任务已发布，位置在梅园西门，请及时查看并接单。",
    related_type: "task",
    related_id: "task-9a01",
    is_read: false,
    read_at: null,
    created_at: ago(6 * MINUTE),
  },
  {
    id: "ntf-1002",
    notification_type: "emergency_task",
    title: "紧急任务提醒",
    content: "桃李园发现一只受伤幼猫，需要就近成员优先响应，点按查看详情。",
    related_type: "task",
    related_id: "task-9a02",
    is_read: false,
    read_at: null,
    created_at: ago(48 * MINUTE),
  },
  {
    id: "ntf-1003",
    notification_type: "task_checkin",
    title: "今日喂食提醒",
    content: "白敬亭，今天的喂食任务记得按时打卡喔～别让小猫等太久。",
    related_type: "task",
    related_id: "task-9a01",
    is_read: false,
    read_at: null,
    created_at: ago(3 * HOUR),
  },
  {
    id: "ntf-1004",
    notification_type: "medicine_updated",
    title: "库存已更新",
    content: "驱虫药（内驱）剩余 5 份，低于安全库存，建议尽快补充。",
    related_type: "medicine",
    related_id: "med-3c11",
    is_read: true,
    read_at: ago(20 * HOUR),
    created_at: ago(23 * HOUR),
  },
  {
    id: "ntf-1005",
    notification_type: "supply_updated",
    title: "物资已补货",
    content: "猫粮 10kg 已上架物资库，现可在梅园物资点领取。",
    related_type: "supply_point",
    related_id: "sup-77a2",
    is_read: true,
    read_at: ago(26 * HOUR),
    created_at: ago(1 * DAY - 2 * HOUR),
  },
  {
    id: "ntf-1006",
    notification_type: "review_approved",
    title: "投喂记录已通过",
    content: "你在 7 月 11 日提交的投喂打卡已通过审核，感谢你的照护。",
    related_type: "task",
    related_id: "task-88f0",
    is_read: true,
    read_at: ago(30 * HOUR),
    created_at: ago(1 * DAY - 30 * MINUTE),
  },
  {
    id: "ntf-1007",
    notification_type: "cat_health_abnormal",
    title: "猫咪健康异常",
    content: "橘座最近三天未被记录出现，且上次观察有打喷嚏迹象，请留意。",
    related_type: "cat",
    related_id: "cat-1e0a",
    is_read: true,
    read_at: ago(2 * DAY),
    created_at: ago(2 * DAY),
  },
  {
    id: "ntf-1008",
    notification_type: "announcement",
    title: "本周值班表已更新",
    content: "本周值班安排已发布，请查收最新排班并确认你的时段。",
    related_type: "announcement",
    related_id: "ann-2026w28",
    is_read: true,
    read_at: ago(3 * DAY),
    created_at: ago(3 * DAY),
  },
];

/**
 * mock 实时推送序列：页面订阅后按节奏“到达”，演示 WebSocket 入站。
 * 每条带一个相对延迟（毫秒）。
 */
export interface MockPush {
  delay_ms: number;
  notification: NotificationItemDto;
}

export function buildMockPushes(startTime: number): MockPush[] {
  return [
    {
      delay_ms: 4200,
      notification: {
        id: "ntf-live-1",
        notification_type: "task_assigned",
        title: "你被指派了新任务",
        content: "管理员将「樱花大道傍晚投喂」指派给你，请在开始前确认。",
        related_type: "task",
        related_id: "task-9b31",
        is_read: false,
        read_at: null,
        created_at: new Date(startTime + 4000).toISOString(),
      },
    },
    {
      delay_ms: 11000,
      notification: {
        id: "ntf-live-2",
        notification_type: "emergency_task",
        title: "紧急：诱捕协助",
        content: "三食堂后侧需要一名成员协助 TNR 诱捕，就近响应更快。",
        related_type: "task",
        related_id: "task-9b32",
        is_read: false,
        read_at: null,
        created_at: new Date(startTime + 10800).toISOString(),
      },
    },
  ];
}
