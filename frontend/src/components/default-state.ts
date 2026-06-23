import notFoundIllustration from "../../素材/svg/缺省页/404黑洞.svg";
import emptyLocationIllustration from "../../素材/svg/缺省页/地址空空的.svg";
import permissionDeniedIllustration from "../../素材/svg/缺省页/您没有权限.svg";
import emptySearchIllustration from "../../素材/svg/缺省页/搜索结果为空.svg";
import emptyDataIllustration from "../../素材/svg/缺省页/数据空空如也.svg";
import underDevelopmentIllustration from "../../素材/svg/缺省页/正在紧急开发.svg";
import imageErrorIllustration from "../../素材/svg/缺省页/图片加载失败.svg";
import networkErrorIllustration from "../../素材/svg/缺省页/网络加载异常.svg";
import emptyRecordsIllustration from "../../素材/svg/缺省页/记录空空的.svg";
import emptyMessagesIllustration from "../../素材/svg/缺省页/消息空荡荡的.svg";

export type DefaultStateKey =
  | "under_development"
  | "empty_data"
  | "empty_records"
  | "empty_search"
  | "network_error"
  | "permission_denied"
  | "not_found"
  | "empty_location"
  | "image_error"
  | "empty_messages";

export interface DefaultStateAction {
  label: string;
  icon?: string;
}

export interface DefaultStatePreset {
  key: DefaultStateKey;
  eyebrow: string;
  title: string;
  description: string;
  illustration: string;
  primaryAction?: DefaultStateAction;
  secondaryAction?: DefaultStateAction;
}

export const DEFAULT_STATE_PRESETS: Record<DefaultStateKey, DefaultStatePreset> = {
  under_development: {
    key: "under_development",
    eyebrow: "正在开发",
    title: "功能建设中",
    description: "这块内容正在整理，稍后就会和大家见面。",
    illustration: underDevelopmentIllustration,
    primaryAction: {
      label: "先去地图看看",
      icon: "map",
    },
    secondaryAction: {
      label: "刷新一下",
      icon: "refresh",
    },
  },
  empty_data: {
    key: "empty_data",
    eyebrow: "暂时没有数据",
    title: "数据空空如也",
    description: "这里的内容还在整理中，稍后刷新试试看。",
    illustration: emptyDataIllustration,
    primaryAction: {
      label: "刷新一下",
      icon: "refresh",
    },
    secondaryAction: {
      label: "返回首页",
      icon: "home",
    },
  },
  empty_records: {
    key: "empty_records",
    eyebrow: "还没有记录",
    title: "记录空空的",
    description: "完成一次任务后，就会在这里留下足迹。",
    illustration: emptyRecordsIllustration,
    primaryAction: {
      label: "去接任务",
      icon: "paw",
    },
    secondaryAction: {
      label: "返回首页",
      icon: "home",
    },
  },
  empty_search: {
    key: "empty_search",
    eyebrow: "没搜到喵",
    title: "搜索结果为空",
    description: "换个关键词、花色或区域试试，也许小猫就在下一个结果里。",
    illustration: emptySearchIllustration,
    primaryAction: {
      label: "重新搜索",
      icon: "search",
    },
    secondaryAction: {
      label: "查看全部",
      icon: "grid",
    },
  },
  network_error: {
    key: "network_error",
    eyebrow: "网络打盹了",
    title: "网络加载异常",
    description: "连接好像有点不稳定，请检查网络后再试一次。",
    illustration: networkErrorIllustration,
    primaryAction: {
      label: "重新连接",
      icon: "wifi",
    },
    secondaryAction: {
      label: "稍后再试",
      icon: "clock",
    },
  },
  permission_denied: {
    key: "permission_denied",
    eyebrow: "权限不足",
    title: "您没有权限",
    description: "当前页面仅对特定成员开放，如需访问，请联系管理员协助处理。",
    illustration: permissionDeniedIllustration,
    primaryAction: {
      label: "返回上一页",
      icon: "home",
    },
    secondaryAction: {
      label: "联系管理员",
      icon: "user",
    },
  },
  not_found: {
    key: "not_found",
    eyebrow: "页面走丢了",
    title: "404 黑洞",
    description: "你访问的页面好像钻进纸箱里啦，先回首页看看其他内容吧。",
    illustration: notFoundIllustration,
    primaryAction: {
      label: "返回首页",
      icon: "home",
    },
    secondaryAction: {
      label: "重新加载",
      icon: "refresh",
    },
  },
  empty_location: {
    key: "empty_location",
    eyebrow: "还没找到位置",
    title: "地址空空的",
    description: "这里暂时还没有地点信息，去地图逛逛，或者新增一个位置吧。",
    illustration: emptyLocationIllustration,
    primaryAction: {
      label: "去地图看看",
      icon: "map",
    },
    secondaryAction: {
      label: "新增位置",
      icon: "pin",
    },
  },
  image_error: {
    key: "image_error",
    eyebrow: "图片走丢了",
    title: "图片加载失败",
    description: "当前图片没有成功显示，检查网络后重新加载吧。",
    illustration: imageErrorIllustration,
    primaryAction: {
      label: "重新加载",
      icon: "refresh",
    },
    secondaryAction: {
      label: "返回上一页",
      icon: "back",
    },
  },
  empty_messages: {
    key: "empty_messages",
    eyebrow: "消息空荡荡的",
    title: "暂无消息",
    description: "有新的任务提醒或系统通知时，会出现在这里。",
    illustration: emptyMessagesIllustration,
    primaryAction: {
      label: "去看看任务",
      icon: "paw",
    },
    secondaryAction: {
      label: "返回首页",
      icon: "home",
    },
  },
};

export const DEFAULT_TAB_PAGE_STATES = {
  map: "under_development",
  cats: "under_development",
  tasks: "under_development",
  profile: "under_development",
} as const;

export function getDefaultStatePreset(
  stateKey: DefaultStateKey,
): DefaultStatePreset {
  return DEFAULT_STATE_PRESETS[stateKey] ?? DEFAULT_STATE_PRESETS.empty_data;
}
