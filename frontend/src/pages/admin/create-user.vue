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
            <picker mode="selector" :range="departments" :value="departmentIndex" @change="onDepartmentChange">
              <view class="picker-field">
                <text>{{ form.department }}</text>
                <text class="picker-arrow">⌄</text>
              </view>
            </picker>
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

          <label class="switch-row">
            <switch :checked="form.must_change_password" color="#2f8037" @change="onMustChangePasswordChange" />
            <text>首次登录必须修改密码</text>
          </label>
        </view>

        <button class="submit-button" :loading="isSubmitting" @tap="submitCreateUser">新增成员</button>

        <view v-if="createdAccount" class="result-card">
          <text class="result-title">成员已新增</text>
          <text class="result-line">喵喵号：{{ createdAccount.meow_no }}</text>
          <text class="result-line">初始密码：{{ createdPassword }}</text>
          <text class="result-tip">请提醒成员首次登录后立即修改密码。</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import { createAdminUser, type AdminCreateUserResponse } from "@/api/admin-users";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import type { UserRole } from "@/types/user";

const departments = ["生存保障部", "活动部", "宣传部", "秘书部", "养护部"] as const;
type Department = (typeof departments)[number];
const roles: UserRole[] = ["member", "summer_volunteer", "admin"];
const roleLabels = ["普通成员", "暑期志愿者", "管理员"];

const userStore = useUserStore();
const isSubmitting = ref(false);
const createdAccount = ref<AdminCreateUserResponse | null>(null);
const createdPassword = ref("");

const form = reactive<{
  meow_no: string;
  initial_password: string;
  nickname: string;
  department: Department;
  role: UserRole;
  must_change_password: boolean;
}>({
  meow_no: "",
  initial_password: "",
  nickname: "",
  department: departments[0],
  role: "member" as UserRole,
  must_change_password: true,
});

const departmentIndex = computed(() => {
  const index = departments.findIndex((department) => department === form.department);
  return index >= 0 ? index : 0;
});
const roleIndex = computed(() => roles.findIndex((role) => role === form.role));

function onDepartmentChange(event: any) {
  const index = Number(event.detail.value);
  form.department = departments[index] || departments[0];
}

function onRoleChange(event: any) {
  const index = Number(event.detail.value);
  form.role = roles[index] || "member";
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
  try {
    const response = await createAdminUser(
      {
        meow_no: form.meow_no || undefined,
        initial_password: form.initial_password || undefined,
        role: form.role,
        profile: {
          nickname: form.nickname,
          department: form.department,
        },
        must_change_password: form.must_change_password,
      },
      accessToken,
    );
    createdAccount.value = response;
    createdPassword.value = form.initial_password || response.meow_no;
    uni.showToast({ title: "账户已创建", icon: "success" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "创建失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isSubmitting.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}
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
.submit-button::after {
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
</style>
