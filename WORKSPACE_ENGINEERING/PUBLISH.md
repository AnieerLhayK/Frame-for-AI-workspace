# 公开仓库发布与维护

本页面向维护公开投影的 agent 和开发者。公开仓库是 Workspace 源文件的派生结果；
发布器与目标的唯一登记来源是 [agent_governance.yaml](../shared/governance/agent_governance.yaml)。
交付条件、授权与失败处理由 [Git 集成政策](../shared/governance/git_integration_policy.md) 规定。

## 发布流程

1. 在 `dev` 修改投影源或生成规则，运行所属任务的验证与 workflow check。
2. 按集成政策审阅完整批次并合入、推送 `main`。发布时保留活动的
   `external_write` TASK，发布源须与已推送的 `main` 一致。
3. 使用登记聚合发布器生成、验证并同步公开投影：

   ```powershell
   python -m scripts.publishing.sync_public_projections --record-id <TASK-ID> --agent codex --push
   ```

4. 核对各发布器的结果。验证、推送或授权失败时停止交付，保留诊断证据，
   修复原件后重试。成功后按政策完成 TASK 和审计回执的有限结项。

指定目标、预览及其他参数以 `sync_public_projections --help` 为准。单仓库适配器由
聚合发布器调用，不在本页重复维护其选项表。

## 源文件与 staging

Frame 是可运行的架构模板，保留文档型扩展入口，不分发私有 skill 或业务代码。
其他公开投影按各自登记契约选择内容。`publish_policy.py` 拥有 Frame 的排除与
路径匿名化规则，`public_workspace_renderer.py` 拥有生成内容，`publish_public.py`
负责文件投影，`publish_check.py` 验证产物与可运行性。

公开 checkout 仅用于一次性生成、验证和推送，不是长期维护副本。临时材料放在
manifest 的 staging 根；成功后清理。排错暂留的 checkout 也应在排错结束后清理。
所有修补回到 Workspace 源文件，不直接修改公开 checkout。

公开根目录的入门、初始化和路径映射文档来自 `USAGE_GUIDES/QUICK_START/`。
路径变量见 [路径映射参考](../USAGE_GUIDES/QUICK_START/path_mapping_reference.md)。

## 排错参考

- 路径泄漏或文件选择错误：修正 `publish_policy.py` 的替换、scrub 或排除规则；
  增加对应行为检查，然后重新生成。不要在产物上修补。
- 缺失文件、导入或测试失败：核查新增模块是否被投影以及相关检查是否适合公开
  环境。以 `publish_check` 结果为证据，不把测试失败笼统视为预期情况。
- 推送失败：核对登记远端、权限与远端提交；按 Git 集成政策处理分歧，
  不强推。涉及 workflow 的鉴权错误应修复所用推送通道的权限。
- 保留预览以排错：先读对应发布器 `--help`，限定 staging 与目标；排错后删除
  本次临时材料，避免累积第二套源文件。
