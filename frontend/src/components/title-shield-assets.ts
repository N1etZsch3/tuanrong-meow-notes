import type { TitleKey } from "@/constants/titles";

import activityDeputy from "../../素材/svg/头衔/盾牌-活动部副部长.svg";
import activityHead from "../../素材/svg/头衔/盾牌-活动部部长.svg";
import careDeputy from "../../素材/svg/头衔/盾牌-养护部副部长.svg";
import careHead from "../../素材/svg/头衔/盾牌-养护部部长.svg";
import president from "../../素材/svg/头衔/盾牌-会长.svg";
import publicityDeputy from "../../素材/svg/头衔/盾牌-宣传部副部长.svg";
import publicityHead from "../../素材/svg/头衔/盾牌-宣传部部长.svg";
import secretaryDeputy from "../../素材/svg/头衔/盾牌-秘书部副部长.svg";
import secretaryHead from "../../素材/svg/头衔/盾牌-秘书部部长.svg";
import survivalDeputy from "../../素材/svg/头衔/盾牌-生存保障部副部长.svg";
import survivalHead from "../../素材/svg/头衔/盾牌-生存保障部部长.svg";
import vicePresident from "../../素材/svg/头衔/盾牌-副会长.svg";

export const TITLE_SHIELD_ASSETS: Record<TitleKey, string> = {
  president,
  vice_president: vicePresident,
  survival_head: survivalHead,
  survival_deputy: survivalDeputy,
  activity_head: activityHead,
  activity_deputy: activityDeputy,
  publicity_head: publicityHead,
  publicity_deputy: publicityDeputy,
  secretary_head: secretaryHead,
  secretary_deputy: secretaryDeputy,
  care_head: careHead,
  care_deputy: careDeputy,
};
