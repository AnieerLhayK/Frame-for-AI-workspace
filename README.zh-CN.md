# Frame-for-AI-workspace

这是一个可部署的受治理 AI 工作区框架模板，包含架构、策略、路由工具和
便携式初始化脚本。

## 边界

- 不包含任何 character system 产品包。
- `skills/` 与 `external-skills/` 只是空的扩展插槽。
- 不包含私人语料、个人角色、既有第三方 skill 或运行时记忆。
- 不提供现成角色，也不替任何模型或平台配置凭据。

## 开始使用

```bash
python scripts/setup_public_workspace.py
python scripts/workspace_cli.py health
python -m pytest scripts/tests -q
```

请先阅读 `BEGINNER_GUIDE.md` 和 `PATH_MAPPING_REFERENCE.md`，再添加本地
skill 或平台集成。凭据和私有源文件应放在仓库之外。
