// 帮助与反馈页的纯数据与类型（按功能拆分，页面只负责渲染）。
// 本页为纯静态内容，不依赖任何后端接口。联系方式为占位，待协会提供真实信息后替换。

export interface HelpFaqItem {
  question: string;
  answer: string;
}

export interface HelpContactItem {
  label: string;
  value: string;
}

export const HELP_FAQ_ITEMS: HelpFaqItem[] = [
  {
    question: "怎么加入团绒猫协、拿到喵喵号？",
    answer:
      "喵喵号由协会管理员统一创建。加入协会后，管理员会为你开通账号并告知初始喵喵号与密码，首次登录后请及时在「设置 - 重设密码」中修改密码。",
  },
  {
    question: "忘记密码了怎么办？",
    answer:
      "请联系协会管理员，在人员管理中为你重置密码。重置后会要求你下次登录时重新设置新密码。",
  },
  {
    question: "怎么修改我的昵称、部门或联系方式？",
    answer:
      "在「喵的」页点击顶部资料卡进入个人资料页即可修改昵称、部门和联系方式。头像更换后需通过内容审核才会生效。",
  },
  {
    question: "任务打卡记录能删除吗？",
    answer:
      "任务打卡是任务完成的凭证，涉及共享的任务记录。个人记录页的展示整理能力会在后续版本开放，如有误操作请先联系管理员处理。",
  },
  {
    question: "微信换了/想解绑当前微信怎么办？",
    answer:
      "在「设置 - 微信解绑」中可自助解绑。解绑后需要使用喵喵号和密码重新登录，并绑定新的微信。",
  },
];

export const HELP_CONTACT_ITEMS: HelpContactItem[] = [
  { label: "协会邮箱", value: "（待协会补充）" },
  { label: "负责同学微信", value: "（待协会补充）" },
  { label: "线下活动室", value: "（待协会补充）" },
];

export const HELP_FEEDBACK_NOTICE =
  "如遇账号、任务或功能问题，欢迎通过以上方式联系协会管理员。反馈提交功能将在后续版本开放。";
