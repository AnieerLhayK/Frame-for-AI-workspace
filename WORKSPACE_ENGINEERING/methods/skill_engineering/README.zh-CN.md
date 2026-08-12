# 技能工程

技能工程是工作区工程（Workspace Engineering）的一个子域，关注可复用 AI 技能的设计、实现、评估、维护与演进。

使用此层处理以下事项：

- 技能的职责与权限边界；
- 提示词与调用设计；
- 运行时诊断与维护循环；
- 漂移预防与风格对齐；
- 决定何时局部修复应升级为生成器或框架行为。

工作区级别的关注点，如 Agent 注册、Git 边界、平台投影、会话连续性、输出路由以及仓库治理，归属于父层 `WORKSPACE_ENGINEERING/`。

当前参考文件：

- `skill_design_patterns.md`
- `prompt_engineering.md`
- `runtime_loop_patterns.md`
- `drift_patterns.md`
- `style_alignment.md`
- `evolution_patterns.md`
