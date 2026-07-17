"""通知类型与展示频道的映射（镜像前端 messages-page.ts TYPE_TO_CHANNEL）。"""

NOTIFICATION_CHANNELS = (
    "task",
    "feeding",
    "medicine",
    "supply",
    "member",
    "cat",
    "announcement",
)

TYPE_TO_CHANNEL: dict[str, str] = {
    "new_task": "task",
    "emergency_task": "task",
    "task_joined": "task",
    "task_assigned": "task",
    "assignment_accepted": "task",
    "assignment_rejected": "task",
    "task_full": "task",
    "task_abandoned": "task",
    "task_checkin": "feeding",
    "review_approved": "member",
    "review_rejected": "member",
    "cat_health_abnormal": "cat",
    "supply_updated": "supply",
    "medicine_updated": "medicine",
    "announcement": "announcement",
}


def channel_for_type(notification_type: str) -> str:
    return TYPE_TO_CHANNEL.get(notification_type, "announcement")
