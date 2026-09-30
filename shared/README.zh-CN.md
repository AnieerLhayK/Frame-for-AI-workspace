# Shared 工作区规则

`shared/` 保存可复用的工作区治理与协议入口。这些文件是源材料，不是生成报告；
manifest 和 package 协议 manifest 仍是注册关系与归属关系的事实源。

## 结构

- `governance/`：Agent 身份、权限、注册和 Git 集成治理。
- `workspace/`：工作区规则、路径解析、发现、失败处理和可移植性。
- `operations/`：报告、交付输出和会话连续性。
- `shared/packages/`：只保存 package 归属索引。package 协议正文仍位于各 package
  的 canonical `packages/<package-id>/shared/` 目录。
- `schemas/`：工作区级可复用 schema。
- `templates/`：工作区级请求与注册模板。
- `claude/`：可选的 Claude Code 策略库。

协议索引见 `INDEX.md`；package-local shared 边界见
`packages/character-system/README.zh-CN.md`。
