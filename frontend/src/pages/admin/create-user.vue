<template>
  <view class="create-page">
    <scroll-view class="create-scroll" scroll-y>
      <view class="create-inner">
        <view class="nav-row">
          <button class="back-button" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">新增成员</text>
            <text class="nav-subtitle">创建成员喵喵号</text>
          </view>
        </view>

        <view class="form-card">
          <view class="field-group">
            <text class="field-label">喵喵号</text>
            <input
              v-model.trim="form.meow_no"
              class="field-input"
              placeholder="留空自动生成 trmx+四位序号"
              maxlength="8"
            />
          </view>

          <view class="field-group">
            <text class="field-label">初始密码</text>
            <input
              v-model.trim="form.initial_password"
              class="field-input"
              password
              placeholder="留空时默认与喵喵号一致"
              maxlength="20"
            />
          </view>

          <view class="field-group">
            <text class="field-label">昵称</text>
            <input v-model.trim="form.nickname" class="field-input" maxlength="20" placeholder="可留空" />
          </view>

          <view class="field-group">
            <text class="field-label">部门</text>
            <DepartmentTagPicker v-model="form.departments" placeholder="请添加部门" />
          </view>

          <view class="field-group">
            <text class="field-label">角色</text>
            <picker mode="selector" :range="roleLabels" :value="roleIndex" @change="onRoleChange">
              <view class="picker-field">
                <text>{{ roleLabels[roleIndex] }}</text>
                <text class="picker-arrow">⌄</text>
              </view>
            </picker>
          </view>

          <view v-if="isPresident" class="field-group">
            <text class="field-label">头衔</text>
            <picker
              mode="selector"
              :range="titleOptions"
              range-key="label"
              :value="titleIndex"
              @change="onTitleChange"
            >
              <view class="picker-field">
                <text>{{ titleOptions[titleIndex]?.label || "无头衔" }}</text>
                <text class="picker-arrow">⌄</text>
              </view>
            </picker>
            <text v-if="titleCatalogError" class="field-hint is-error">{{ titleCatalogError }}</text>
          </view>

          <label class="switch-row">
            <switch :checked="form.must_change_password" color="#2f8037" @change="onMustChangePasswordChange" />
            <text>首次登录必须修改密码</text>
          </label>
        </view>

        <button
          class="submit-button"
          :disabled="isSubmitting || isRestoring"
          :loading="isSubmitting"
          @tap="submitCreateUser"
        >
          新增成员
        </button>

        <view v-if="createdAccount" class="result-card">
          <text class="result-title">
            {{ resultMode === "restored" ? "账号已重新启用" : "成员已新增" }}
          </text>
          <text class="result-line">喵喵号：{{ createdAccount.meow_no }}</text>
          <text class="result-line">初始密码：{{ createdPassword }}</text>
          <text class="result-tip">
            {{
              resultMode === "restored"
                ? "原资料和历史记录已保留，请成员使用新密码登录并重新绑定微信。"
                : "请提醒成员首次登录后立即修改密码。"
            }}
          </text>
        </view>
      </view>
    </scroll-view>

    <view v-if="restoreConflict" class="restore-modal-mask" @tap="closeRestoreModal">
      <view class="restore-modal-card" @tap.stop>
        <view class="restore-modal-accent" />
        <view class="restore-modal-heading">
          <view class="restore-modal-icon-shell">
            <image class="restore-modal-icon" :src="restorePawIcon" mode="aspectFit" />
          </view>
          <view class="restore-modal-heading-copy">
            <text class="restore-modal-kicker">发现历史账号</text>
            <text class="restore-modal-title">这个喵喵号用过啦</text>
          </view>
        </view>

        <text class="restore-modal-intro">
          喵喵号 {{ restoreConflict.meow_no }} 已关联一条删除记录，请确认是否重新启用原账号。
        </text>

        <view class="restore-account-card">
          <view class="restore-account-row">
            <text class="restore-account-label">喵喵号</text>
            <text class="restore-account-value">{{ restoreConflict.meow_no }}</text>
          </view>
          <view class="restore-account-divider" />
          <view class="restore-account-row">
            <text class="restore-account-label">历史昵称</text>
            <text class="restore-account-value restore-account-nickname">
              {{ restoreConflict.nickname || "未设置昵称" }}
            </text>
          </view>
        </view>

        <view class="restore-modal-note">
          <view class="restore-modal-note-dot" />
          <text>重新启用原账号会保留原资料和历史记录，并重置密码、清除旧微信绑定。</text>
        </view>
        <text class="restore-modal-warning">
          不会使用本页新填写的昵称、部门和角色；恢复后可在人员详情中修改。
        </text>

        <view class="restore-modal-actions">
          <button
            class="restore-modal-cancel"
            :disabled="isRestoring"
            hover-class="restore-button-hover"
            @tap="closeRestoreModal"
          >
            换个喵喵号
          </button>
          <button
            class="restore-modal-confirm"
            :disabled="isRestoring"
            :loading="isRestoring"
            hover-class="restore-button-hover"
            @tap="confirmRestoreAccount"
          >
            重新启用
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import {
  createAdminUser,
  restoreAdminUser,
  type AdminCreateUserResponse,
} from "@/api/admin-users";
import { getTitleCatalog, type TitleCatalogItem } from "@/api/titles";
import type { UserTitle } from "@/constants/titles";
import {
  parseDeletedAccountConflict,
  type DeletedAccountConflict,
} from "@/pages/admin/deleted-account-restore";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import type { UserRole } from "@/types/user";
import DepartmentTagPicker from "@/components/DepartmentTagPicker.vue";
import { DEPARTMENTS } from "@/constants/departments";

import restorePawIcon from "../../../素材/svg/登录页/猫爪1.svg";

const roles: UserRole[] = ["member", "summer_volunteer", "admin"];
const roleLabels = ["普通成员", "暑期志愿者", "管理员"];

const userStore = useUserStore();
const isSubmitting = ref(false);
const isRestoring = ref(false);
const createdAccount = ref<AdminCreateUserResponse | null>(null);
const createdPassword = ref("");
const resultMode = ref<"created" | "restored" | null>(null);
const restoreConflict = ref<DeletedAccountConflict | null>(null);
const titleCatalogError = ref("");
const titleOptions = ref<Array<{ key: UserTitle; label: string }>>([
  { key: null, label: "无头衔" },
]);
const isPresident = computed(() => userStore.currentUser?.title === "president");

const form = reactive<{
  meow_no: string;
  initial_password: string;
  nickname: string;
  departments: string[];
  role: UserRole;
  must_change_password: boolean;
  title: UserTitle;
}>({
  meow_no: "",
  initial_password: "",
  nickname: "",
  departments: [DEPARTMENTS[0]],
  role: "member" as UserRole,
  must_change_password: true,
  title: null,
});

const roleIndex = computed(() => roles.findIndex((role) => role === form.role));
const titleIndex = computed(() =>
  Math.max(0, titleOptions.value.findIndex((item) => item.key === form.title)),
);

function onRoleChange(event: any) {
  const index = Number(event.detail.value);
  form.role = roles[index] || "member";
}

function onTitleChange(event: any) {
  form.title = titleOptions.value[Number(event.detail.value) || 0]?.key ?? null;
}

async function loadTitleOptions() {
  if (!isPresident.value) {
    form.title = null;
    titleOptions.value = [{ key: null, label: "无头衔" }];
    return;
  }
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    return;
  }
  titleCatalogError.value = "";
  try {
    const response = await getTitleCatalog(accessToken);
    const available = response.items.filter(
      (item: TitleCatalogItem) => item.key !== "president" && item.is_available,
    );
    titleOptions.value = [
      { key: null, label: "无头衔" },
      ...available.map((item) => ({ key: item.key, label: item.label })),
    ];
    if (!titleOptions.value.some((item) => item.key === form.title)) {
      form.title = null;
    }
  } catch (error) {
    titleCatalogError.value = error instanceof Error ? error.message : "头衔列表加载失败";
    form.title = null;
  }
}

function onMustChangePasswordChange(event: any) {
  form.must_change_password = Boolean(event.detail.value);
}

function validateForm(): boolean {
  if (form.meow_no && !/^trmx\d{4}$/.test(form.meow_no)) {
    uni.showToast({ title: "喵喵号格式应为 trmx0001", icon: "none" });
    return false;
  }
  if (form.initial_password && !/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9@_!]{8,20}$/.test(form.initial_password)) {
    uni.showToast({ title: "密码需 8-20 位，含字母和数字", icon: "none" });
    return false;
  }
  if (!form.departments.length) {
    uni.showToast({ title: "请至少添加一个部门", icon: "none" });
    return false;
  }
  return true;
}

async function submitCreateUser() {
  if (isSubmitting.value || !validateForm()) {
    return;
  }
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isSubmitting.value = true;
  createdAccount.value = null;
  resultMode.value = null;
  try {
    const response = await createAdminUser(
      {
        meow_no: form.meow_no || undefined,
        initial_password: form.initial_password || undefined,
        role: form.role,
        profile: {
          nickname: form.nickname,
          departments: form.departments,
          title: isPresident.value ? form.title : null,
        },
        must_change_password: form.must_change_password,
      },
      accessToken,
    );
    createdAccount.value = response;
    createdPassword.value = form.initial_password || response.meow_no;
    resultMode.value = "created";
    uni.showToast({ title: "账户已创建", icon: "success" });
  } catch (error) {
    const conflict = parseDeletedAccountConflict(error);
    if (conflict) {
      restoreConflict.value = conflict;
      return;
    }
    const message = error instanceof Error ? error.message : "创建失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function closeRestoreModal() {
  if (isRestoring.value) {
    return;
  }
  restoreConflict.value = null;
}

async function confirmRestoreAccount() {
  const conflict = restoreConflict.value;
  if (!conflict || isRestoring.value) {
    return;
  }
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isRestoring.value = true;
  try {
    const response = await restoreAdminUser(accessToken, conflict.user_id, {
      initial_password: form.initial_password || undefined,
    });
    createdAccount.value = response;
    createdPassword.value = form.initial_password || response.meow_no;
    resultMode.value = "restored";
    restoreConflict.value = null;
    uni.showToast({ title: "账号已重新启用", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "重新启用失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isRestoring.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

onShow(() => {
  void loadTitleOptions();
});
</script>

<style scoped>
.create-page {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfcfb 0%, #f5faef 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.create-scroll {
  height: 100vh;
}

.create-inner {
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

.back-button {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #ffffff;
  color: #2f8037;
  font-size: 58rpx;
  line-height: 54rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.1);
}

.back-button::after,
.submit-button::after,
.restore-modal-cancel::after,
.restore-modal-confirm::after {
  border: 0;
}

.nav-title,
.nav-subtitle {
  display: block;
}

.nav-title {
  color: #171b22;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #68717a;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  line-height: 1.2;
}

.form-card,
.result-card {
  margin-top: 40rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
  padding: 30rpx;
}

.field-group + .field-group {
  margin-top: 28rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: #20242a;
  font-size: 27rpx;
  font-weight: 900;
}

.field-hint {
  display: block;
  margin-top: 10rpx;
  color: #6e7780;
  font-size: 22rpx;
}

.field-hint.is-error {
  color: #c34839;
}

.field-input,
.picker-field {
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

.picker-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-arrow {
  color: #717982;
  font-size: 34rpx;
}

.switch-row {
  margin-top: 30rpx;
  color: #4d555f;
  display: flex;
  align-items: center;
  gap: 18rpx;
  font-size: 25rpx;
}

.submit-button {
  height: 88rpx;
  margin-top: 34rpx;
  border-radius: 28rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 88rpx;
}

.result-title,
.result-line,
.result-tip {
  display: block;
}

.result-title {
  color: #20242a;
  font-size: 31rpx;
  font-weight: 900;
}

.result-line {
  margin-top: 16rpx;
  color: #303740;
  font-size: 26rpx;
}

.result-tip {
  margin-top: 18rpx;
  color: #6e7780;
  font-size: 23rpx;
}

.restore-modal-mask {
  position: fixed;
  z-index: 100;
  inset: 0;
  box-sizing: border-box;
  padding: 44rpx 32rpx calc(env(safe-area-inset-bottom) + 44rpx);
  background: rgba(20, 38, 24, 0.5);
  backdrop-filter: blur(10rpx);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: restore-mask-in 180ms ease-out both;
}

.restore-modal-card {
  position: relative;
  box-sizing: border-box;
  width: 680rpx;
  max-width: 100%;
  padding: 46rpx 40rpx 38rpx;
  border: 2rpx solid rgba(211, 230, 202, 0.96);
  border-radius: 40rpx;
  background:
    radial-gradient(circle at 92% 4%, rgba(244, 218, 177, 0.38), transparent 190rpx),
    radial-gradient(circle at 4% 12%, rgba(206, 235, 196, 0.72), transparent 190rpx),
    linear-gradient(180deg, #ffffff 0%, #fbfff8 100%);
  box-shadow: 0 32rpx 88rpx rgba(19, 54, 26, 0.24);
  overflow: hidden;
  animation: restore-modal-in 240ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.restore-modal-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 12rpx;
  background: linear-gradient(90deg, #cce9bd 0%, #5ca253 58%, #efc98f 100%);
}

.restore-modal-heading {
  display: flex;
  align-items: center;
  gap: 22rpx;
}

.restore-modal-icon-shell {
  width: 82rpx;
  height: 82rpx;
  border-radius: 26rpx;
  background: linear-gradient(145deg, #e9f7e2 0%, #d7edcc 100%);
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.restore-modal-icon {
  width: 46rpx;
  height: 46rpx;
  transform: rotate(-12deg);
}

.restore-modal-heading-copy {
  min-width: 0;
}

.restore-modal-kicker,
.restore-modal-title,
.restore-modal-intro,
.restore-modal-warning {
  display: block;
}

.restore-modal-kicker {
  color: #6a8c61;
  font-size: 22rpx;
  font-weight: 800;
  letter-spacing: 3rpx;
}

.restore-modal-title {
  margin-top: 6rpx;
  color: #1f4726;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.2;
}

.restore-modal-intro {
  margin-top: 28rpx;
  color: #52605a;
  font-size: 25rpx;
  line-height: 1.7;
}

.restore-account-card {
  margin-top: 24rpx;
  padding: 4rpx 24rpx;
  border: 2rpx solid rgba(204, 224, 196, 0.78);
  border-radius: 26rpx;
  background: rgba(244, 250, 240, 0.82);
}

.restore-account-row {
  min-height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.restore-account-divider {
  height: 2rpx;
  background: rgba(188, 211, 180, 0.55);
}

.restore-account-label {
  color: #738076;
  font-size: 23rpx;
  flex: 0 0 auto;
}

.restore-account-value {
  min-width: 0;
  color: #223e28;
  font-size: 27rpx;
  font-weight: 900;
  text-align: right;
  word-break: break-all;
}

.restore-account-nickname {
  color: #2f8037;
}

.restore-modal-note {
  margin-top: 24rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: rgba(231, 245, 224, 0.9);
  color: #3f5d43;
  font-size: 23rpx;
  line-height: 1.55;
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.restore-modal-note-dot {
  width: 12rpx;
  height: 12rpx;
  margin-top: 10rpx;
  border-radius: 50%;
  background: #5a9d51;
  box-shadow: 0 0 0 8rpx rgba(90, 157, 81, 0.12);
  flex: 0 0 auto;
}

.restore-modal-warning {
  margin-top: 18rpx;
  color: #916f43;
  font-size: 21rpx;
  line-height: 1.55;
}

.restore-modal-actions {
  margin-top: 30rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18rpx;
}

.restore-modal-cancel,
.restore-modal-confirm {
  height: 82rpx;
  margin: 0;
  padding: 0;
  border-radius: 26rpx;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 82rpx;
}

.restore-modal-cancel {
  border: 2rpx solid #d7e4d2;
  background: rgba(247, 250, 245, 0.96);
  color: #5e6d61;
}

.restore-modal-confirm {
  border: 2rpx solid #2f8037;
  background: linear-gradient(135deg, #58a24e 0%, #2f8037 100%);
  color: #ffffff;
  box-shadow: 0 14rpx 28rpx rgba(47, 128, 55, 0.22);
}

.restore-button-hover {
  opacity: 0.88;
  transform: translateY(2rpx);
}

@keyframes restore-mask-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes restore-modal-in {
  from {
    opacity: 0;
    transform: translateY(26rpx) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
