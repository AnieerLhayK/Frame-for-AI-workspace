# 公开仓库发布与维护

## 概述

本 workspace 维护一个公开 GitHub 仓库 `Frame-for-AI-workspace`，包含架构骨架、可运行脚本、权限模型和经验文档。公开仓库是私有工作区的**派生快照**，不含任何 skill 代码或业务敏感数据。

- **公开仓库**: https://github.com/AnieerLhayK/Frame-for-AI-workspace
- **生成脚本**: `scripts/publish_public.py`
- **验证脚本**: `scripts/publish_check.py`
- **维护脚本**: `scripts/sync_public_repo.py`

## 维护边界

`Frame-for-AI-workspace` 只保留 GitHub 远端作为长期仓库。本 workspace 不维护一个
独立的本地部署副本；同步脚本创建的本地 clone 只是可丢弃 staging，用于生成、验证和
推送公开快照。

默认 staging 位置由 `PUBLIC_STAGING_DIR` 控制；未设置时优先使用
`AI_TOOL_STAGING_DIR` 下的 `Frame-for-AI-workspace`，再退回系统临时目录。不要把
staging 当作源代码维护面。

## 首次发布

首次发布已通过以下流程完成：

```powershell
# 1. 生成 scrubbed 快照
python scripts/publish_public.py --out-dir ${STAGING_DIR}

# 2. 验证
python scripts/publish_check.py --dir ${STAGING_DIR}

# 3. 创建 GitHub 仓库
gh repo create Frame-for-AI-workspace --public --description "..."

# 4. 推送
cd ${STAGING_DIR}
git remote add origin git@github.com:AnieerLhayK/Frame-for-AI-workspace.git
git push -u origin main
```

## 增量同步

当 main 分支上发生了"安全变更"后，使用维护脚本一键同步：

```powershell
# 检查模式（默认）—— 生成并验证但不推送
python scripts/sync_public_repo.py

# 推送模式 —— 生成 + 验证 + 提交 + 推送
python scripts/sync_public_repo.py --push

# 跳过测试（更快）
python scripts/sync_public_repo.py --push --skip-tests
```

### 前置条件

- 本地 workspace git 工作区干净（无未提交变更）
- 如果确实有未提交变更需要同步，使用 `--force-dirty`
- 已配置 SSH 推送权限（`git@github.com:AnieerLhayK/Frame-for-AI-workspace.git`）

## 何时同步

### 触发同步的变更

- `shared/` 协议文件变更（policy、registry、governance）
- `scripts/` 核心脚本变更（非 skill 相关）
- `.claude/` 边界配置变更（rules、project-boundary）
- `AGENTS.md` / `ARCHITECTURE.md` 变更
- `task_registry.yaml` / `prompt_registry.yaml` 变更
- `.github/workflows/` CI 配置变更

### 不触发同步的变更

- `skills/` 下任何变更 —— 已完全排除
- `packages/` 业务代码变更 —— 已骨架化
- `reports/` 自动生成的快照报告
- `${DATA_ROOT}` 下的任何数据文件 —— 在 workspace 之外
- 任何 gitignored 的文件

## 路径匿名化

脚本 `publish_public.py` 自动替换所有机器特定路径。举例如下：

| 示例路径（部分） | 替换为 |
|------------------|--------|
| `<drive>:\AI\workspace` | `${WORKSPACE_ROOT}` |
| `<drive>:\AI\data` | `${DATA_ROOT}` |
| `<drive>:\Dev` | `${DEV_ROOT}` |
| `<drive>:\ztemp` | `${SCRATCH_ROOT}` |
| `<drive>:\Users\<user>` | `${USER_HOME}` |

完整规则见 `PATH_MAPPING_REFERENCE.md`。

## 目录骨架化

`packages/character-system/` 下的业务代码被清除，保留目录结构并替换为说明性 stub 文件：

- `README.md` — 该目录的用途说明
- `SKILL.md` — skill 注册信息模板
- `SHARED_PROTOCOLS.md` — 该 domain 的协议指引

使用者可以基于这些 stub 填入自己的技能实现。

## 验证清单

发布前检查：

- [ ] 无 `<drive>:\AI` 或 `<drive>:/AI` 硬编码路径
- [ ] 无 `<drive>:\Users\<user>` 硬编码路径
- [ ] `skills/` 目录不存在
- [ ] 模板文件（`.template`）齐全
- [ ] 自动化文档（`BEGINNER_GUIDE.md`, `PATH_MAPPING_REFERENCE.md`, `ONBOARDING.md`）存在
- [ ] 新手初始化脚本 `scripts/setup_public_workspace.py` 存在
- [ ] 核心脚本可运行（task list, explain mechanism, agent list, health）
- [ ] 核心测试通过（193+ 项）
- [ ] CI workflow 兼容 Linux

## 故障排除

### push 被拒绝

```
! [remote rejected] main -> main (refusing to allow an OAuth App to create or update workflow ...)
```

**原因**: GitHub OAuth token 缺少 `workflow` scope。

**解决**: 使用 SSH 协议推送（已配置），或手动添加 scope：

```powershell
gh auth refresh --hostname github.com --scopes workflow
```

### 验证失败

查看具体问题类型：

```powershell
python scripts/publish_check.py --dir <staging-dir> --skip-tests
```

常见原因：
- 新增了含绝对路径的文件，需要加入 `SUBSTITUTIONS` 或 `SCRUB_FILES`
- 新增了需要排除的目录，加入 `EXCLUDED_PATHS`
- 测试依赖基础设施（Hermes、OpenCode、Reasonix），属于预期失败
