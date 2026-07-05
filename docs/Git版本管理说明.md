# Git 版本管理说明

这份文档是给项目维护者看的，不是给 Git 考试看的。

## 先说结论

这份文档第一次编写时，仓库还没有完全按推荐的版本管理方式来。

当时检查到的状态是：

- 当前分支是 `main`。
- `main` 最新提交是 `532cb22 chore: save current workspace changes`。
- `dev` 分支存在，但它落后 `main` 83 个提交，说明现在实际开发主要堆到了 `main` 上。
- 有很多 `feature/*`、`fix/*`、`codex/*` 分支，说明以前是按任务分支开发过的。
- 当前没有任何 Git tag，所以还没有用 Git 正式标记 `1.0.0`。
- 当前没有配置 remote，`git remote -v` 没有输出。
- 当前工作区不是干净的：`AGENTS.md` 和 `docs/开发进度.md` 有修改，另有一个未跟踪文档 `docs/团绒喵记本_小程序隐私保护指引补充文档.txt`。

所以当时更准确的说法是：仓库已经有分支管理的雏形，但还没有形成“上线版本可追踪、补丁可回滚、后续开发不污染线上”的稳定流程。

落地完成后的标准状态应该是：

- `origin` 指向 GitHub 远程仓库。
- `main` 已推送到远程，代表当前线上稳定基线。
- `dev` 已同步到 `main`，作为下一轮开发集成分支。
- `v1.0.0` tag 已推送到远程，用来标记第一个线上版本。
- 真实服务器地址、域名、地图 Key、小程序 AppID、云存储配置等不再写死在仓库里，真实值只放在本地 `.env`、部署参数、云平台配置或私有环境中。

## 我建议你以后记住四句话

1. `main` 永远代表线上稳定版。
2. `dev` 是下一版功能的集合地。
3. 每次上线都打一个 `v版本号` 标签。
4. 线上出问题，从 `main` 拉 `hotfix`，修完合回 `main`，也要合回 `dev`。

够了。大部分时间你只要记住这四句。

## 分支应该怎么用

### main

`main` 是线上分支。

它应该尽量保持干净、稳定、可部署。不要把半成品直接提交到 `main`。

以后看到 `main`，你心里可以把它翻译成：

```text
这是现在或者最近一次可以上线的代码。
```

### dev

`dev` 是开发集成分支。

新功能、优化、下一版内容，先合到 `dev`。等到准备发新版时，再从 `dev` 拉一个发布分支。

现在你的 `dev` 已经明显落后 `main`，后面应该先把 `main` 同步回 `dev`，不然它会越来越像一个废弃分支。

可以这样做：

```bash
git switch dev
git merge main
```

如果你不想继续维护 `dev`，也可以明确决定不用它。但如果要按稳定流程来，我建议保留 `dev`。

### feature/*

新功能用 `feature/*`。

例子：

```text
feature/notifications
feature/duty-assignment
feature/cat-observations
```

新功能一般从 `dev` 拉：

```bash
git switch dev
git pull
git switch -c feature/notifications
```

做完后合回 `dev`，不要直接合进 `main`。

### fix/*

普通 bug 修复用 `fix/*`。

如果这个 bug 不紧急，不影响线上用户，就从 `dev` 拉，修完合回 `dev`。

例子：

```text
fix/map-marker-display
fix/task-photo-preview
```

### hotfix/*

线上已经出问题，必须尽快修，用 `hotfix/*`。

这个分支必须从 `main` 拉，因为它修的是线上版本。

例子：

```bash
git switch main
git pull
git switch -c hotfix/1.0.1-login-token
```

修完以后：

1. 合回 `main`。
2. 打 `v1.0.1` 标签。
3. 再把同一个修复合回 `dev`。

这样线上修好了，下一版开发分支也不会漏掉这个修复。

### release/*

准备发新版时，用 `release/*`。

例子：

```text
release/1.1.0
```

这个分支的意思是：

```text
功能先别乱加了，现在只修发版前发现的问题。
```

发版成功后，把它合进 `main`，然后打 tag。

## 版本号怎么定

用这种格式：

```text
主版本.次版本.补丁版本
```

也就是：

```text
1.0.0
1.0.1
1.1.0
2.0.0
```

人话解释：

- `1.0.1`：修 bug，不加大功能。
- `1.1.0`：加功能，但不推翻原来的东西。
- `2.0.0`：大改，可能不兼容以前的接口、数据或使用方式。

当前项目已经上线第一个版本，所以现在是：

```text
1.0.0
```

后续如果只是修线上 bug，就是：

```text
1.0.1
1.0.2
```

如果要做通知中心、排班指派这种下一阶段能力，更适合发：

```text
1.1.0
```

## 现在最该补的一件事：打 v1.0.0 标签

Git tag 的作用很简单：

```text
告诉所有人：这个提交就是 1.0.0。
```

以后线上出问题，你才能很快知道“当时上线的到底是哪份代码”。

注意：`v1.0.0` 应该打在实际上线的代码提交上，不一定是今天写文档之后的提交。

如果你确认线上部署的就是当前 `main` 的 `532cb22`，可以这样补：

```bash
git switch main
git tag -a v1.0.0 532cb22 -m "release: v1.0.0"
```

如果以后配置了远程仓库，再推上去：

```bash
git push origin v1.0.0
```

如果你不确定线上部署的是不是 `532cb22`，先不要打 tag。先去服务器、部署记录或当时的提交记录里确认。

## 每次上线前做什么

上线前至少确认这些：

```bash
git status --short --branch
```

工作区应该是干净的，最好不要有 `M` 或 `??`。

然后跑项目需要的检查，例如：

```bash
python -m pytest backend/tests -q
python -m ruff check backend/app backend/tests
npm run type-check
npm run test -- --run
npm run build:mp-weixin
```

不是每次都必须一模一样，但上线前一定要知道自己验证了什么，没有验证什么。

## 每次上线后做什么

上线成功后：

1. 确认线上跑的是哪个 commit。
2. 给这个 commit 打 tag，比如 `v1.0.1`。
3. 更新 `docs/开发进度.md`。
4. 记录验证结果、部署说明、回滚方式。

不要只在脑子里记。过两周以后，人脑会开始胡说八道，Git 不会。

## 这次落地时哪些文件应该提交

这次落地版本管理方案时，应该提交这些内容：

```text
AGENTS.md
docs/开发进度.md
docs/Git版本管理说明.md
脱敏后的示例配置、部署脚本和相关测试
```

提交时显式添加这些文件，不要用 `git add .`。

```bash
git add AGENTS.md docs/开发进度.md docs/Git版本管理说明.md
git add backend/.env.example backend/app/core/config.py backend/tests/test_map_api.py
git add frontend/.env.example frontend/project.config.json frontend/src/manifest.json frontend/src/config/app-env.ts
git add frontend/tests/config/miniapp-config.test.ts frontend/tests/pages/tasks-page.test.ts
git add scripts/bootstrap-server-ssh-key.ps1 scripts/deploy-backend.ps1 scripts/test-deployment-contracts.ps1 deploy/nginx/catmap.conf
git add docs/Prompt/地图模块.md docs/模块功能/COS图片上传功能流程设计文档.md docs/plans/2026-07-02-backend-deployment*.md
git commit -m "chore(git): establish post-release workflow"
```

如果还有 `docs/团绒喵记本_小程序隐私保护指引补充文档.txt` 这种未跟踪文件，先不要顺手提交。它要不要进 Git，需要你判断：

- 如果它是项目正式文档，可以单独提交。
- 如果里面有敏感信息，先别提交。
- 如果只是临时文件，可以继续保持未跟踪，或者放进忽略规则。

这个项目里文件多，顺手一加很容易把不该进仓库的东西加进去。

## 推荐的下一步

按顺序来：

1. 先确认线上 1.0.0 对应的 commit。
2. 给那个 commit 打 `v1.0.0` 标签。
3. 把当前文档更新提交掉。
4. 如果继续使用 `dev`，把 `main` 合回 `dev`。
5. 以后新功能从 `dev` 拉 `feature/*`。
6. 线上急修从 `main` 拉 `hotfix/*`。

这样你的仓库就会从“能用”变成“出事也能找回现场”。
