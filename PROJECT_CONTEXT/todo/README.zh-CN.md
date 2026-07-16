# Todo 索引

这个目录集中记录尚未完成或由条件触发的工作，并把 workspace 自身优化与
外来 skill 的内化工作分开管理。

- [`workspace-optimization.md`](workspace-optimization.md)：workspace 原生的架构、治理、prompt library、character-system 以及延后的优化工作。
- [`external-skills.md`](external-skills.md)：记录 `workspace_manifest.yaml -> external_roots.raw_skills` 下发现的每一个原始 skill 来源，以及来源、兼容性、适配、验证和注册状态。

常驻规则仍应放在 `AGENTS.md`、`PROJECT_CONTEXT/context_budget.md` 和
`shared/` 策略中，而不是重复写成待办。发现新的原始 skill 后，必须先把
它加入 `external-skills.md`，再开始评估或适配。
