# Hermes 技能审批与回退

本文面向 Hermes 使用者与 Workspace 宿主维护者。技能日常审核在 Hermes
聊天或交互 CLI 中进行；部署与回退从 Workspace 根目录运行。权限依据
[Agent governance policy](../../shared/governance/agent_governance_policy.md)，
本页不授予技能注册、Workspace 源码或投影修改权限。

## 审核一个变更

1. Hermes 仅在有明确复用价值时简短建议；同意准备后，它可以生成具体待审变更。
2. 输入 `/skills pending` 查看编号，再输入 `/skills diff <id>` 审核内容。
3. 输入 `/skills approve <id>` 应用该项，或 `/skills reject <id>` 拒绝。

创建、修改、删除和支持文件操作都经过此流程。一次只审核一个操作；不支持
`approve all`。未批准前技能文件不变，重复批准不重复应用。待审内容、原始
文件、Workspace 注册或实际目标变化后，必须拒绝旧项并重新准备。
聊天中超过显示长度的 diff 不能视为完整审核；应在交互 CLI 查看同一编号的
完整 `/skills diff <id>` 后再批准。

Workspace 登记的技能、投影、链接及同名遮蔽不进入私有审批路径。
只有明确归属 Hermes 的本地技能可维护；内置、Hub 和来源不明的技能不自动接管。
后台复盘与 curator 不再产生技能草稿，长期记忆保留原行为。

## 健康与故障

```powershell
python -m scripts.workspace.hermes_skill_deployment status
workspace health
```

`approval` 表示逐项审批模式；`blocked` 表示恢复旧服务后的禁写模式。
`FAIL` 不得解释为审批正常：检查适配器签名、进程生命周期、hook 与设置。
原生终端、代码执行和浏览器原始执行接口不能绕过技能审批；只读检查仍可用。

每次应用先保存完整恢复证据，再要求原生账本记录变更后状态。原生操作部分
失败或账本失败时原地恢复旧文件。若恢复本身无法完成，停止技能写入，并保留
`state/skill-recovery-<id>.json` 中的原生 checkpoint 引用，交给 Codex 维护。
不自动丢弃未完成恢复的数据或覆盖后续人工修改。

## 维护与安全回退

部署 CLI 仅接受 `hermes_skill_approval` 类型、Codex 所有且声明
`external_write` 的活跃 TASK，并限定本机已批准的 Hermes 与工作台目标。
先运行隔离原生测试、插件加载验证和双版本 SQLite 兼容验证，通过后才切换。
不安装其他版本，不直接修改 vendor 源，不跟随技能链接备份 Workspace。

部署记录返回精确备份目录。需要恢复时，使用该目录与当前活跃维护 TASK：

```powershell
python -m scripts.workspace.hermes_skill_deployment rollback --record-id <TASK-ID> --backup <backup-path>
```

该命令精确停止匹配实例，恢复已校验的旧设置并重新施加禁写限制，再启动旧服务。
它不会用旧数据库快照覆盖切换后收到的新消息。回退保留聊天、网页检索和长期
记忆，关闭技能、终端、文件、代码、代理委派、浏览器及 MCP 工具，直到维护完成。
数据库不兼容或尚有活跃工作时不切换；停机后的快照或启动失败也进入自动恢复。

备份与恢复证据保留在本机专用备份目录，不进入公开投影。测试产物仅使用 staging，
成功使用后删除。现有技能的清理不属于部署或回退的授权范围。
