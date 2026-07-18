<template>
  <view class="member-detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">成员资料</text>
            <text class="nav-subtitle">{{ readonlyMode ? "管理员账号仅可查看" : "编辑成员基础信息" }}</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-card">
          <text>正在加载成员资料...</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-card is-error">
          <text>{{ errorMessage || "成员资料加载失败" }}</text>
        </view>

        <view v-else class="detail-content">
          <view class="avatar-panel">
            <view class="avatar-shell" @tap="chooseAvatar">
              <image
                class="avatar"
                :src="avatarDisplay"
                mode="aspectFill"
                @error="avatarLoadFailed = true"
              />
              <text v-if="!readonlyMode" class="avatar-plus">+</text>
            </view>
            <text class="avatar-note">
              {{ readonlyMode ? "管理员账号资料不可修改" : "点击更换头像，图片不超过 2MB" }}
            </text>
            <text v-if="avatarReviewHint" class="avatar-review-hint">{{ avatarReviewHint }}</text>
          </view>

          <view class="form-card">
            <view class="field-group">
              <text class="field-label">昵称</text>
              <input
                v-model.trim="form.nickname"
                class="field-input"
                maxlength="20"
                :disabled="readonlyMode"
                placeholder="请输入昵称"
              />
            </view>
            <view class="field-group">
              <text class="field-label">真实姓名</text>
              <input
                v-model.trim="form.real_name"
                class="field-input"
                maxlength="20"
                :disabled="readonlyMode"
                placeholder="可选"
              />
            </view>
            <view class="field-group">
              <text class="field-label">部门</text>
              <DepartmentTagPicker
                v-model="form.departments"
                :disabled="readonlyMode"
                placeholder="请添加部门"
              />
            </view>
            <view class="field-group">
              <text class="field-label">年级</text>
              <input
                v-model.trim="form.grade"
                class="field-input"
                maxlength="12"
                :disabled="readonlyMode"
                placeholder="例如 2025"
              />
            </view>
            <view class="field-group">
              <text class="field-label">联系方式</text>
              <input
                v-model.trim="form.contact_info"
                class="field-input"
                maxlength="32"
                :disabled="readonlyMode"
                placeholder="手机号或微信号"
              />
            </view>
            <view class="field-group">
              <text class="field-label">喵喵号</text>
              <view class="readonly-field">{{ userDetail?.meow_no || "--" }}</view>
            </view>
            <view class="field-group">
              <text class="field-label">当前头衔</text>
              <view class="readonly-field title-current">
                <TitleBadge :title="userDetail?.profile.title" />
                <text v-if="!userDetail?.profile.title" class="title-empty">无头衔</text>
              </view>
            </view>
            <view class="field-group">
              <text class="field-label">身份</text>
              <picker
                :disabled="readonlyMode"
                :range="roleOptions"
                range-key="label"
                :value="roleIndex"
                @change="selectRole"
              >
                <view class="picker-field">
                  <text class="picker-value">{{ currentRoleLabel }}</text>
                  <text v-if="!readonlyMode" class="picker-arrow">⌄</text>
                </view>
              </picker>
            </view>
            <view class="field-group">
              <text class="field-label">账号状态</text>
              <picker
                :disabled="readonlyMode"
                :range="statusOptions"
                range-key="label"
                :value="statusIndex"
                @change="selectStatus"
              >
                <view class="picker-field">
                  <text class="picker-value">{{ currentStatusLabel }}</text>
                  <text v-if="!readonlyMode" class="picker-arrow">⌄</text>
                </view>
              </picker>
            </view>
          </view>

          <view v-if="canManageTitles" class="title-actions-card">
            <text class="title-actions-heading">头衔管理</text>
            <text class="title-actions-note">仅会长可操作；已被占用的头衔不会出现在选择器中。</text>
            <picker
              v-if="titleOptions.length"
              mode="selector"
              :range="titleOptions"
              range-key="label"
              :value="0"
              :disabled="isTitleActionPending"
              @change="selectAssignableTitle"
            >
              <view class="title-action-button is-primary">授予或变更头衔</view>
            </picker>
            <button
              v-if="canRevokeTargetTitle"
              class="title-action-button"
              :disabled="isTitleActionPending"
              @tap="confirmRevokeTitle"
            >
              剥夺当前头衔
            </button>
            <button
              class="title-action-button is-transfer"
              :disabled="isTitleActionPending"
              @tap="confirmPresidentTransfer"
            >
              转让会长
            </button>
            <text v-if="titleCatalogError" class="title-actions-error">{{ titleCatalogError }}</text>
          </view>

          <view v-if="!readonlyMode" class="detail-actions">
            <button
              class="account-actions-button"
              :disabled="isAccountActionPending"
              hover-class="button-hover"
              @tap="openAccountActions"
            >
              账号操作
            </button>
            <button
              class="save-button"
              :disabled="isAccountActionPending"
              :loading="isSaving"
              hover-class="button-hover"
              @tap="saveMember"
            >
              保存资料
            </button>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="resetVisible" class="modal-mask" @tap="closeResetModal">
      <view class="modal-panel" @tap.stop>
        <text class="modal-title">重置成员密码</text>
        <text class="modal-hint">重置后成员下次登录需要修改密码。</text>
        <input
          v-model.trim="resetPassword"
          class="modal-input"
          password
          maxlength="20"
          placeholder="请输入新密码"
        />
        <view class="modal-actions">
          <button class="modal-cancel" hover-class="button-hover" @tap="closeResetModal">
            取消
          </button>
          <button
            class="modal-confirm"
            :loading="isResetting"
            hover-class="button-hover"
            @tap="submitResetPassword"
          >
            重置
          </button>
        </view>
      </view>
    </view>
    <!-- #ifdef MP-WEIXIN -->
    <page-container
      :show="pageLeaveGuardArmed"
      :overlay="false"
      :duration="0"
      @beforeleave="handleNativePageLeave"
      @afterleave="handleGuardContainerAfterLeave"
    />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import {
  clearAdminUserWechatBinding,
  deleteAdminUser,
  getAdminUserDetail,
  resetAdminUserPassword,
  updateAdminUser,
  type AdminUserDto,
} from "@/api/admin-users";
import { resolveUserAvatarContentUrl, uploadUserAvatar } from "@/api/files";
import {
  getTitleCatalog,
  setMemberTitle,
  transferPresident,
  type TitleCatalogItem,
} from "@/api/titles";
import type { UserTitle } from "@/constants/titles";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import { consumeAvatarReviewFailureNotice } from "@/utils/avatar-review-notice";
import {
  createPageContainerLeaveCoordinator,
  createPageLeaveGuard,
  type PageContainerLeaveAction,
  type PageLeaveOrigin,
} from "@/utils/page-leave-guard";

import DepartmentTagPicker from "@/components/DepartmentTagPicker.vue";
import TitleBadge from "@/components/TitleBadge.vue";
import defaultAvatar from "../../../../素材/svg/萌猫/橘猫.svg";
import loadingBackground from "../../../../素材/加载页素材/背景.jpg";
import {
  createMemberEditSnapshot,
  hasUnsavedMemberChanges,
  type MemberEditSnapshot,
} from "./member-edit-guard";
import {
  availableAssignableTitles,
  canManageMemberTitles,
} from "./title-actions";

type PickerChangeEvent = { detail: { value: string | number } };

const AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024;
const ACCOUNT_ACTIONS = ["重置密码", "重置微信绑定", "删除账号"] as const;
const roleOptions = [
  { label: "成员", value: "member" },
  { label: "暑期志愿者", value: "summer_volunteer" },
  { label: "管理员", value: "admin" },
];
const statusOptions = [
  { label: "正常", value: "active" },
  { label: "禁用", value: "blocked" },
  { label: "离会", value: "left" },
];

const userStore = useUserStore();
const userId = ref("");
const userDetail = ref<AdminUserDto | null>(null);
const avatarUrl = ref<string | null>(null);
const avatarReviewStatus = ref<"idle" | "pending" | "passed" | "rejected" | "failed">("idle");
const loadState = ref<"loading" | "ready" | "error">("loading");
const errorMessage = ref("");
const isSaving = ref(false);
const resetVisible = ref(false);
const resetPassword = ref("");
const isResetting = ref(false);
const isClearingWechatBinding = ref(false);
const isDeleting = ref(false);
const isTitleActionPending = ref(false);
const titleCatalog = ref<TitleCatalogItem[]>([]);
const titleCatalogError = ref("");
const savedMemberSnapshot = ref<MemberEditSnapshot | null>(null);
const nativePageLeaveGuardReady = ref(true);
const isNavigatingAway = ref(false);
const isGuardContainerClosing = ref(false);

const form = reactive({
  nickname: "",
  real_name: "",
  departments: [] as string[],
  grade: "",
  contact_info: "",
  role: "member",
  status: "active",
});

const readonlyMode = computed(() => !userDetail.value?.editable);
const canManageTitles = computed(() =>
  canManageMemberTitles(
    userStore.currentUser?.title,
    userStore.currentUser?.id,
    userDetail.value?.id,
  ),
);
const titleOptions = computed(() =>
  availableAssignableTitles(titleCatalog.value, userDetail.value?.id || ""),
);
const canRevokeTargetTitle = computed(() => {
  const title = userDetail.value?.profile.title;
  return Boolean(title && title !== "president");
});
const canResetPassword = computed(() => Boolean(userDetail.value?.can_reset_password));
const avatarLoadFailed = ref(false);
const isAccountActionPending = computed(
  () =>
    isSaving.value ||
    isResetting.value ||
    isClearingWechatBinding.value ||
    isDeleting.value ||
    isTitleActionPending.value,
);
const avatarPreview = computed(() => avatarUrl.value || userDetail.value?.profile.avatar_url || defaultAvatar);
const avatarDisplay = computed(() => (avatarLoadFailed.value ? defaultAvatar : avatarPreview.value));
const avatarReviewHint = computed(() => {
  if (avatarReviewStatus.value === "pending") {
    return "图片已上传，审核通过后自动生效";
  }
  return "";
});

watch(avatarPreview, () => {
  avatarLoadFailed.value = false;
});
const roleIndex = computed(() => Math.max(0, roleOptions.findIndex((item) => item.value === form.role)));
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === form.status)));
const currentRoleLabel = computed(() => roleOptions[roleIndex.value]?.label || "成员");
const currentStatusLabel = computed(() => statusOptions[statusIndex.value]?.label || "正常");
const pageLeaveGuard = createPageLeaveGuard(
  () => !isSaving.value && hasPendingMemberChanges(),
);
const pageLeaveCoordinator = createPageContainerLeaveCoordinator();
const pageLeaveGuardArmed = computed(
  () =>
    nativePageLeaveGuardReady.value &&
    !isNavigatingAway.value &&
    !isSaving.value &&
    hasPendingMemberChanges(),
);

function applyUser(
  user: AdminUserDto,
  options: { preservePendingAvatar?: boolean } = {},
) {
  const preservePendingAvatar = Boolean(
    options.preservePendingAvatar &&
    avatarReviewStatus.value === "pending" &&
    user.profile.avatar_review_status !== "passed",
  );
  userDetail.value = user;
  if (!preservePendingAvatar) {
    avatarUrl.value = resolveUserAvatarContentUrl(user.profile.avatar_url);
    avatarReviewStatus.value = user.profile.avatar_review_status || "idle";
  }
  form.nickname = user.profile.nickname || "";
  form.real_name = user.profile.real_name || "";
  form.departments = user.profile.departments?.length
    ? [...user.profile.departments]
    : user.profile.department
      ? [user.profile.department]
      : [];
  form.grade = user.profile.grade || "";
  form.contact_info = user.profile.contact_info || "";
  form.role = user.role || "member";
  form.status = user.status || "active";
  savedMemberSnapshot.value = createMemberEditSnapshot({
    nickname: form.nickname,
    real_name: form.real_name,
    departments: form.departments,
    grade: form.grade,
    contact_info: form.contact_info,
    role: form.role,
    status: form.status,
    avatar_url: avatarUrl.value,
  });
  pageLeaveGuard.reset();
}

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return null;
  }
  return accessToken;
}

async function loadUser() {
  const token = await getAccessToken();
  if (!token || !userId.value) {
    loadState.value = "error";
    errorMessage.value = "缺少成员 ID";
    return;
  }
  loadState.value = "loading";
  try {
    const user = await getAdminUserDetail(token, userId.value);
    applyUser(user);
    if (canManageTitles.value) {
      await loadTitleCatalog();
    } else {
      titleCatalog.value = [];
      titleCatalogError.value = "";
    }
    if (
      consumeAvatarReviewFailureNotice(
        user.id,
        user.profile.avatar_review_asset_id,
        user.profile.avatar_review_status || "idle",
      )
    ) {
      uni.showToast({ title: "头像审核未通过，请更换图片后重试", icon: "none" });
    }
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value = error instanceof Error ? error.message : "成员资料加载失败";
  }
}

async function loadTitleCatalog() {
  const token = await getAccessToken();
  if (!token || !canManageTitles.value) {
    return;
  }
  titleCatalogError.value = "";
  try {
    titleCatalog.value = (await getTitleCatalog(token)).items;
  } catch (error) {
    titleCatalog.value = [];
    titleCatalogError.value = error instanceof Error ? error.message : "头衔列表加载失败";
  }
}

function selectAssignableTitle(event: PickerChangeEvent) {
  const selected = titleOptions.value[Number(event.detail.value) || 0];
  if (!selected) {
    return;
  }
  confirmSetTitle(selected.key, selected.label);
}

function confirmSetTitle(title: UserTitle, label: string) {
  if (!canManageTitles.value || isTitleActionPending.value) {
    return;
  }
  uni.showModal({
    title: "确认授予头衔",
    content: `确认将“${label}”授予 ${userDetail.value?.profile.nickname || userDetail.value?.meow_no || "该成员"} 吗？`,
    confirmText: "确认授予",
    confirmColor: "#2f8037",
    success: (result) => {
      if (result.confirm) {
        void applyTitle(title);
      }
    },
  });
}

function confirmRevokeTitle() {
  if (!canManageTitles.value || !canRevokeTargetTitle.value || isTitleActionPending.value) {
    return;
  }
  uni.showModal({
    title: "剥夺头衔",
    content: `确认移除 ${userDetail.value?.profile.nickname || "该成员"} 的“${userDetail.value?.profile.title_label || "当前头衔"}”吗？`,
    confirmText: "确认移除",
    confirmColor: "#c34839",
    success: (result) => {
      if (result.confirm) {
        void applyTitle(null);
      }
    },
  });
}

async function applyTitle(title: UserTitle) {
  if (!canManageTitles.value || isTitleActionPending.value || !userId.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isTitleActionPending.value = true;
  try {
    applyUser(await setMemberTitle(token, userId.value, title), {
      preservePendingAvatar: true,
    });
    await loadTitleCatalog();
    uni.showToast({ title: title ? "头衔已更新" : "头衔已移除", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "头衔更新失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isTitleActionPending.value = false;
  }
}

function confirmPresidentTransfer() {
  if (!canManageTitles.value || isTitleActionPending.value) {
    return;
  }
  const targetName = userDetail.value?.profile.nickname || userDetail.value?.meow_no || "该成员";
  const promotionNotice =
    userDetail.value?.role === "admin" || userDetail.value?.role === "super_admin"
      ? ""
      : "接任后该成员会自动成为管理员，原登录令牌会失效。";
  uni.showModal({
    title: "转让会长",
    content: `确认将会长头衔转让给 ${targetName} 吗？转让完成后你将失去头衔。${promotionNotice}`,
    confirmText: "确认转让",
    confirmColor: "#b7791f",
    success: (result) => {
      if (result.confirm) {
        void applyPresidentTransfer();
      }
    },
  });
}

async function applyPresidentTransfer() {
  if (!canManageTitles.value || isTitleActionPending.value || !userId.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isTitleActionPending.value = true;
  try {
    const result = await transferPresident(token, userId.value);
    applyUser(result.successor, { preservePendingAvatar: true });
    await userStore.refreshCurrentUser();
    titleCatalog.value = [];
    uni.showToast({ title: "会长已转让", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "会长转让失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isTitleActionPending.value = false;
  }
}

function selectRole(event: PickerChangeEvent) {
  form.role = roleOptions[Number(event.detail.value) || 0]?.value || "member";
}

function selectStatus(event: PickerChangeEvent) {
  form.status = statusOptions[Number(event.detail.value) || 0]?.value || "active";
}

function chooseAvatar() {
  if (readonlyMode.value) {
    return;
  }
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (result) => {
      const files = (result.tempFiles || []) as Array<{ size?: number }>;
      if (Number(files[0]?.size || 0) > AVATAR_MAX_SIZE_BYTES) {
        uni.showToast({ title: "头像图片不能超过 2MB", icon: "none" });
        return;
      }
      const tempPath = result.tempFilePaths[0];
      if (tempPath) {
        void uploadAvatar(tempPath);
      }
    },
  });
}

async function uploadAvatar(tempPath: string) {
  const token = await getAccessToken();
  if (!token) {
    return;
  }

  uni.showLoading({ title: "头像上传中", mask: true });
  try {
    const asset = await uploadUserAvatar(token, tempPath, userId.value || undefined);
    avatarUrl.value = tempPath;
    avatarReviewStatus.value = asset.security_status === "pending" ? "pending" : "passed";
    if (savedMemberSnapshot.value) {
      savedMemberSnapshot.value = { ...savedMemberSnapshot.value, avatar_url: tempPath };
    }
    uni.hideLoading();
    uni.showToast({ title: asset.review_message || "头像已提交", icon: "none" });
  } catch (error) {
    uni.hideLoading();
    const message = error instanceof Error ? error.message : "头像上传失败";
    uni.showToast({ title: message, icon: "none" });
  }
}

function validateMember(): boolean {
  if (!form.nickname.trim()) {
    uni.showToast({ title: "请输入昵称", icon: "none" });
    return false;
  }
  if (!form.departments.length) {
    uni.showToast({ title: "请至少添加一个部门", icon: "none" });
    return false;
  }
  return true;
}

async function saveMember() {
  if (readonlyMode.value || isSaving.value || !validateMember()) {
    return;
  }
  const token = await getAccessToken();
  if (!token || !userId.value) {
    return;
  }
  isSaving.value = true;
  try {
    const updated = await updateAdminUser(token, userId.value, {
      role: form.role,
      status: form.status,
      profile: {
        nickname: form.nickname.trim(),
        real_name: form.real_name || null,
        departments: form.departments,
        grade: form.grade || null,
        contact_info: form.contact_info || null,
      },
    });
    applyUser(updated, { preservePendingAvatar: true });
    uni.showToast({ title: "成员资料已保存", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSaving.value = false;
  }
}

function openResetModal() {
  resetPassword.value = "";
  resetVisible.value = true;
}

function closeResetModal() {
  if (!isResetting.value) {
    resetVisible.value = false;
  }
}

function openAccountActions() {
  if (readonlyMode.value || isAccountActionPending.value) {
    return;
  }
  uni.showActionSheet({
    itemList: [...ACCOUNT_ACTIONS],
    success: (result) => {
      if (result.tapIndex === 0 && canResetPassword.value) {
        openResetModal();
        return;
      }
      if (result.tapIndex === 1) {
        if (!userDetail.value?.wechat_bound) {
          uni.showToast({ title: "当前成员尚未绑定微信", icon: "none" });
          return;
        }
        confirmClearWechatBinding();
        return;
      }
      if (result.tapIndex === 2) {
        confirmDeleteAccount();
      }
    },
  });
}

async function submitResetPassword() {
  if (resetPassword.value.length < 8) {
    uni.showToast({ title: "密码至少 8 位", icon: "none" });
    return;
  }
  const token = await getAccessToken();
  if (!token || !userId.value) {
    return;
  }
  isResetting.value = true;
  try {
    await resetAdminUserPassword(token, userId.value, {
      new_password: resetPassword.value,
      must_change_password: true,
    });
    resetVisible.value = false;
    uni.showToast({ title: "密码已重置", icon: "success" });
    await loadUser();
  } catch (error) {
    const message = error instanceof Error ? error.message : "重置失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isResetting.value = false;
  }
}

function confirmClearWechatBinding() {
  if (readonlyMode.value || !userDetail.value?.wechat_bound || isClearingWechatBinding.value) {
    return;
  }
  uni.showModal({
    title: "重置微信绑定",
    content: "解绑后，该成员下次需要使用喵喵号和密码重新登录并绑定微信。",
    confirmText: "确认解绑",
    confirmColor: "#b45309",
    success: (result) => {
      if (result.confirm) {
        void clearWechatBinding();
      }
    },
  });
}

async function clearWechatBinding() {
  if (readonlyMode.value || isClearingWechatBinding.value || !userId.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isClearingWechatBinding.value = true;
  try {
    await clearAdminUserWechatBinding(token, userId.value);
    if (userDetail.value) {
      userDetail.value = { ...userDetail.value, wechat_bound: false };
    }
    uni.showToast({ title: "微信绑定已重置", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "微信解绑失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isClearingWechatBinding.value = false;
  }
}

function confirmDeleteAccount() {
  if (readonlyMode.value || isDeleting.value) {
    return;
  }
  uni.showModal({
    title: "删除账号",
    content: "删除后该账号将从人员列表移除，且不能继续登录。请确认是否继续。",
    confirmText: "确认删除",
    confirmColor: "#d14343",
    success: (result) => {
      if (result.confirm) {
        void deleteAccount();
      }
    },
  });
}

async function deleteAccount() {
  if (readonlyMode.value || isDeleting.value || !userId.value) {
    return;
  }
  const token = await getAccessToken();
  if (!token) {
    return;
  }
  isDeleting.value = true;
  try {
    await deleteAdminUser(token, userId.value);
    uni.showToast({ title: "账号已删除", icon: "success" });
    setTimeout(() => {
      uni.redirectTo({ url: "/pages/admin/users/index" });
    }, 350);
  } catch (error) {
    const message = error instanceof Error ? error.message : "删除账号失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isDeleting.value = false;
  }
}

function goBack() {
  if (!hasPendingMemberChanges()) {
    isNavigatingAway.value = true;
    uni.navigateBack();
    return;
  }
  requestPageLeave("button");
}

function hasPendingMemberChanges() {
  if (readonlyMode.value) {
    return false;
  }
  return hasUnsavedMemberChanges(savedMemberSnapshot.value, {
    nickname: form.nickname,
    real_name: form.real_name,
    departments: form.departments,
    grade: form.grade,
    contact_info: form.contact_info,
    role: form.role,
    status: form.status,
    avatar_url: avatarUrl.value,
  });
}

function requestPageLeave(origin: PageLeaveOrigin) {
  const request = pageLeaveGuard.requestLeave();
  if (request === "leave") {
    navigateBackAfterGuard();
    return;
  }
  if (request === "confirm") {
    pageLeaveCoordinator.begin(origin);
    confirmDiscardMemberChanges();
  }
}

function handleNativePageLeave() {
  if (isNavigatingAway.value || isGuardContainerClosing.value) {
    return;
  }
  if (isSaving.value || !hasPendingMemberChanges()) {
    return;
  }
  nativePageLeaveGuardReady.value = false;
  requestPageLeave("container");
}

function navigateBackAfterGuard() {
  if (isNavigatingAway.value) {
    return;
  }
  isNavigatingAway.value = true;
  nativePageLeaveGuardReady.value = false;
  uni.navigateBack({
    fail: () => {
      isNavigatingAway.value = false;
      pageLeaveGuard.reset();
      pageLeaveCoordinator.reset();
      nativePageLeaveGuardReady.value = hasPendingMemberChanges();
      uni.showToast({ title: "返回失败，请重试", icon: "none" });
    },
  });
}

function rearmNativePageLeaveGuard() {
  isNavigatingAway.value = false;
  nativePageLeaveGuardReady.value = hasPendingMemberChanges();
}

function runGuardLeaveAction(action: PageContainerLeaveAction | null) {
  if (action === "navigate") {
    navigateBackAfterGuard();
  } else if (action === "rearm") {
    rearmNativePageLeaveGuard();
  }
}

function resolveGuardLeave(action: PageContainerLeaveAction) {
  const resolution = pageLeaveCoordinator.resolve(action);
  if (resolution.closeContainer) {
    isGuardContainerClosing.value = true;
    nativePageLeaveGuardReady.value = false;
  }
  runGuardLeaveAction(resolution.action);
}

function handleGuardContainerAfterLeave() {
  isGuardContainerClosing.value = false;
  runGuardLeaveAction(pageLeaveCoordinator.afterContainerLeave());
}

function confirmDiscardMemberChanges() {
  uni.showModal({
    title: "放弃修改",
    content: "修改尚未保存，是否放弃？",
    confirmText: "放弃",
    confirmColor: "#d73546",
    cancelText: "继续编辑",
    success: (result) => {
      if (result.confirm && pageLeaveGuard.confirmDiscard()) {
        resolveGuardLeave("navigate");
        return;
      }
      pageLeaveGuard.cancelDiscard();
      resolveGuardLeave("rearm");
    },
  });
}

onLoad(async (query) => {
  userId.value = typeof query?.user_id === "string" ? query.user_id : "";
  try {
    await userStore.refreshCurrentUser();
  } catch {
    // 成员详情请求仍会返回明确的认证错误，避免在这里重复提示。
  }
  await loadUser();
});
</script>

<style scoped>
.member-detail-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #111827;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.detail-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.detail-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.back-button,
.save-button,
.account-actions-button,
.title-action-button,
.modal-cancel,
.modal-confirm {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.save-button::after,
.account-actions-button::after,
.title-action-button::after,
.modal-cancel::after,
.modal-confirm::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.field-label,
.modal-title,
.modal-hint {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.state-card,
.form-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
}

.state-card {
  margin-top: 42rpx;
  padding: 44rpx 30rpx;
  color: #4c555f;
  font-size: 28rpx;
  font-weight: 900;
  text-align: center;
}

.state-card.is-error {
  color: #c34839;
}

.avatar-panel {
  margin: 42rpx 0 26rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-shell {
  position: relative;
}

.avatar {
  width: 164rpx;
  height: 164rpx;
  border: 8rpx solid #ffffff;
  border-radius: 50%;
  background: #edf6e9;
  box-shadow: 0 18rpx 38rpx rgba(42, 63, 43, 0.14);
}

.avatar-plus {
  position: absolute;
  right: 0;
  bottom: 10rpx;
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background: #2f8037;
  color: #ffffff;
  font-size: 36rpx;
  line-height: 46rpx;
  text-align: center;
}

.avatar-note {
  margin-top: 18rpx;
  color: #737b84;
  font-size: 24rpx;
}

.avatar-review-hint {
  margin-top: 10rpx;
  color: #9a6826;
  font-size: 24rpx;
  line-height: 1.5;
  text-align: center;
}

.form-card {
  padding: 30rpx;
}

.field-group + .field-group {
  margin-top: 26rpx;
}

.field-label {
  margin-bottom: 14rpx;
  color: #20242a;
  font-size: 27rpx;
  font-weight: 900;
}

.field-input,
.picker-field,
.readonly-field,
.modal-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 82rpx;
  border: 2rpx solid #dfe5e1;
  border-radius: 22rpx;
  background: #ffffff;
  color: #23272e;
  font-size: 27rpx;
  padding: 0 28rpx;
}

.field-input[disabled],
.picker-field,
.readonly-field {
  background: rgba(247, 251, 239, 0.86);
}

.title-current {
  justify-content: flex-start;
}

.title-empty {
  color: #8a929b;
}

.title-actions-card {
  margin-top: 28rpx;
  padding: 28rpx;
  border: 2rpx solid rgba(203, 222, 197, 0.9);
  border-radius: 26rpx;
  background: rgba(250, 255, 247, 0.96);
}

.title-actions-heading,
.title-actions-note,
.title-actions-error {
  display: block;
}

.title-actions-heading {
  color: #204d28;
  font-size: 29rpx;
  font-weight: 900;
}

.title-actions-note {
  margin-top: 10rpx;
  color: #68756b;
  font-size: 22rpx;
  line-height: 1.5;
}

.title-action-button {
  width: 100%;
  height: 78rpx;
  margin: 18rpx 0 0;
  border: 2rpx solid #6b9c6b;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #37643d;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 78rpx;
}

.title-action-button.is-primary {
  background: #2f8037;
  color: #ffffff;
}

.title-action-button.is-transfer {
  border-color: #c59a3c;
  color: #8a6216;
}

.title-actions-error {
  margin-top: 14rpx;
  color: #c34839;
  font-size: 22rpx;
}

.picker-field,
.readonly-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-placeholder {
  color: #98a0a8;
}

.picker-arrow {
  color: #717982;
  font-size: 34rpx;
}

.detail-actions {
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18rpx;
}

.account-actions-button,
.save-button {
  width: 100%;
  height: 88rpx;
  border-radius: 16rpx;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 88rpx;
}

.account-actions-button {
  border: 2rpx solid #2f8037;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
}

.save-button {
  background: #2f8037;
  color: #ffffff;
}

.modal-mask {
  position: fixed;
  z-index: 20;
  inset: 0;
  background: rgba(17, 24, 39, 0.42);
  display: flex;
  align-items: flex-end;
}

.modal-panel {
  box-sizing: border-box;
  width: 100%;
  padding: 34rpx 34rpx calc(env(safe-area-inset-bottom) + 34rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
}

.modal-title {
  color: #111827;
  font-size: 34rpx;
  font-weight: 900;
}

.modal-hint {
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.modal-input {
  margin-top: 24rpx;
}

.modal-actions {
  margin-top: 26rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 20rpx;
}

.modal-cancel,
.modal-confirm {
  height: 82rpx;
  border-radius: 26rpx;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 82rpx;
}

.modal-cancel {
  background: #eef4ec;
  color: #526070;
}

.modal-confirm {
  background: #287c31;
  color: #ffffff;
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
