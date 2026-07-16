# 工作流 Prompt：诊断运行时漂移

在 `style-doctor` 已曝光的平台上使用。其权限仍仅限于诊断。

```text
使用 style-doctor。

运行时故障：
<描述发生了什么>

角色：
<角色 id>

任务类型：
<任务类型>

失败输出片段：
<片段>

预期方向：
<预期的风格或行为>

请：
1. 分类漂移类型。
2. 识别失败的层面。
3. 引用证据。
4. 指定严重程度。
5. 建议修补范围。
6. 生成诊断包文。
7. 如果需要维护者工作，生成 handoff 包文。

不要修补文件。
不要创建 patch note、validation note、generalization note 或 patch ledger 条目。
不要标记 accepted/rejected/deferred；将维护者决定留给 character-maintainer。
在 handoff 建议中使用工作区相对路径。
```
