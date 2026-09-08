# Frame-for-AI-workspace

这是一个可部署的受治理 AI 工作区框架模板，包含架构、策略、路由工具和
便携式初始化脚本。
使用 `workspace_manifest.yaml` 配置路径和权限。

## 扩展

- `skills/`：添加为当前工作区开发的技能。
- `external-skills/`：添加经过审查的第三方技能。
- `mcp/`：保存 MCP 连接所需的可复用配置模板。
- `packages/`：按领域组织相关的技能、策略和实现代码。

扩展目录提供添加所需组件的说明或配置模板。

## 开始使用

```bash
python scripts/setup_public_workspace.py
python -m scripts.workspace.workspace_cli health
python -m pytest scripts/tests -q
```

请先阅读 `BEGINNER_GUIDE.md` 和 `PATH_MAPPING_REFERENCE.md`，再添加本地
skill 或平台集成。凭据和私有源文件应放在仓库之外。

