# style-doctor Prompt 模板

当前曝光：OpenCode。曝光权限不包含源码修补。

## 安全的纯文本诊断

当模型可能较弱、文件访问存在风险或你希望零源文件变更时使用。

```text
使用 style-doctor。

诊断此运行时漂移，但不要写入或修改任何文件。
仅输出包文文本。

源角色：
<角色 id，例如 zyc>

用户反馈：
"<反馈内容>"

失败输出片段：
<片段>

预期风格方向：
<应有哪些不同>

防护措施：
- 不要修补源文件。
- 不要更新任何 ledger。
- 不要创建 patch note、validation note 或 generalization note。
- 不要标记 accepted/rejected/deferred。
- 如果需要维护者工作，仅以文本形式包含 handoff 包文。
```

## 诊断运行时漂移

```text
使用 style-doctor。

源角色：
<角色 id，例如 zyc>

源技能路径：
<绝对路径，如已知>

任务类型：
<rewrite | continuation | imitation | critique | style_transfer | other>

用户反馈：
"<反馈内容>"

失败输出片段：
<片段>

预期风格方向：
<应有哪些不同>

任务：
分类漂移类型，识别失败的层面，生成诊断包文。

防护措施：
- 不要直接修补源文件。
- 不要创建 patch note、validation note 或 generalization note。
- 不要更新 `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`。
- 不要将任何 patch 标记为 `accepted`、`rejected`、`deferred`、`applied` 或 `validated`。
- 不要修改 character-generator、character-maintainer、共享协议或工作区 manifest 文件。
- 不要泛化角色特定的经验。
- 在 handoff 建议中使用工作区相对路径，而非平台投影路径。
- 如果需要维护者，生成 handoff 包文。

输出：
- diagnosis_id
- 漂移类型
- 失败层面
- 证据
- 严重程度
- 建议修补范围
- do_not_touch
- 下一负责人
```

## 准备 Handoff 给维护者

```text
使用 style-doctor。

诊断：
<诊断包文或摘要>

目标维护者：
character-maintainer

任务：
创建供维护者审查的 handoff 包文。

包含：
- handoff_id
- diagnosis_id
- character_id
- handoff 原因
- 建议检查的文件
- 建议修补类型
- 风险等级
- 验收标准
- 待定问题

防护措施：
- 不要修补源文件。
- 不要写入 patch note、validation note 或 generalization note。
- 不要编辑 `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`。
- 不要标记 accepted/rejected/deferred；该决定属于 character-maintainer。
- 在 `recommended_files_to_inspect` 中使用工作区相对路径。
```
