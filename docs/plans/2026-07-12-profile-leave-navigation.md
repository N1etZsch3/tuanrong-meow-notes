# Profile Leave Navigation Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the permanent intermediate navigation layer from every guarded profile form while preserving dirty-form confirmation, and rename the profile home title to “喵的”.

**Architecture:** Keep the actual page outside `page-container`. Derive whether the native guard is armed from the current dirty snapshot, and let clean navigation bypass the shared leave state machine entirely. Reuse the existing guard only for dirty confirmation and release it before the final `navigateBack`.

**Tech Stack:** uni-app, Vue 3, TypeScript, WeChat Mini Program `page-container`, Vitest.

---

### Task 1: Lock the regression with tests

**Files:**
- Modify: `frontend/tests/pages/profile-page.test.ts`
- Modify: `frontend/tests/pages/admin-page.test.ts`

1. Assert both guarded pages render their real root before the standalone `page-container`.
2. Assert the guard `show` state is derived from unsaved changes and starts closed.
3. Assert clean button navigation directly calls `uni.navigateBack()` without requesting guard confirmation.
4. Assert the profile home title is exactly “喵的”.
5. Run the two test files and confirm they fail against the permanent wrapper implementation.

### Task 2: Implement conditional native leave guards

**Files:**
- Modify: `frontend/src/pages/profile/detail.vue`
- Modify: `frontend/src/pages/admin/users/detail.vue`
- Modify: `frontend/src/pages/profile/index.vue`
- Modify: `frontend/src/utils/page-leave-guard.ts` only if tests show the shared state machine needs adjustment

1. Move each page root outside `page-container` and leave a standalone empty guard component.
2. Derive guard visibility from loaded dirty state; never arm it for a clean form.
3. Make explicit back navigate immediately when clean and use confirmation only when dirty.
4. Ensure cancel rearms only while still dirty; ensure confirm closes the guard before final navigation.
5. Change the profile home title to “喵的”.
6. Run targeted tests until green, then run relevant profile/admin test files.

### Task 3: Verify, document, and integrate

**Files:**
- Modify: `docs/开发进度.md`

1. Run all frontend tests, type check, and `build:mp-weixin`.
2. Run `git diff --check` and review the diff for unrelated files or sensitive data.
3. Commit the fix branch, merge it into `.worktrees/dev`, and rerun the relevant checks on `dev`.
4. Execute the authorized backend deployment from `dev`, verify migration head and deployed `/api/v1/health`, and record any external WeChat configuration blocker without exposing secrets.
