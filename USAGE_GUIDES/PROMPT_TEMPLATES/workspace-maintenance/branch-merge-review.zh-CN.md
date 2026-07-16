# 分支合并审查

在将工作区维护分支合并到 `main` 之前使用此 prompt。

```text
任务：
审查此分支是否已准备好合并到 `main`：
<分支名称>

开始：
1. 运行 `git status --short --branch --untracked-files=all`。
2. 运行 `git log --oneline --decorate --left-right --cherry-pick main...HEAD`。
3. 运行 `git diff --name-status main...HEAD`。
4. 识别该分支所代表的任务 id 和验证命令。

防护措施：
- 在用户明确批准之前不要合并。
- 在合并完成且工作树清理干净之前不要删除分支。
- 当分支线性领先于 `main` 时，优先使用 fast-forward 合并。
- 如果分支和 `main` 都更改了 task ledger、todo 或 usage guides，在合并前检查这些文件。
- 除非明确要求，否则不要推送。

预期输出：
- 分支与 `main` 的关系。
- 提交列表。
- 风险文件或可能的冲突。
- 已运行的验证和仍需的验证。
- 建议的 merge、rebase 或 hold 决定。
```
