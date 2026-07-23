# PROJECT_CONTEXT

`PROJECT_CONTEXT/` 是 workspace 的记忆与路由门面。manifest、shared 政策、
源代码和生成报告分别对各自的事实负责。

## 启动接口

- `context_index.yaml`：机器可读的职责目录和读取规则；
- `README.md` / `README.zh-CN.md`：人工导航和边界说明；
- `workspace summary` 与 `workspace explain`：面向 AI 和开发者的实时摘要。

## 职责目录

- `continuity/`：当前状态、会话交接和受保护迁移；
- `governance/`：上下文预算与变更面政策；
- `documentation/`：canonical Markdown 伴侣登记表；
- `memory/`：长期决策与术语表；
- `references/`：外部项目边界记录；
- `tasks/`：任务路由、结构化记录和日期台账；
- `knowledge/`：主题索引与主题条目；
- `potential_for_future/`：活动选项、风险及其历史；
- `todo/`：未完成或触发式工作；
- `reports/`：上下文报告；`history/` 默认不进入启动上下文。

根部 registry YAML 兼容投影已于 2026-07-19 正式废弃。请直接使用
`tasks/registry/index.yaml`、`knowledge/index.yaml` 与
`documentation/doc_pair_registry.yaml`。历史台账和报告可以保留当时真实的
路径文字，但它们不是活动路由或别名。

## 工作流

1. 阅读根 `AGENTS.md`，检查 Git 状态并解析精确任务。
2. 只读取解析器要求的上下文。
3. 在 workspace 或外部写入前启动任务记录。
4. 修改最窄的权威源层，并保持 manifest 权威。
5. 结案前运行路由验证与 `workspace workflow check`。

编辑 Markdown 时使用 `PROJECT_CONTEXT/documentation/doc_pair_registry.yaml`，
并同步已登记的 `.zh-CN.md` 伴侣。
