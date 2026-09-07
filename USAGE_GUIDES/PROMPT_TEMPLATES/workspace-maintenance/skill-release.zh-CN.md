# Skill 发布

从 Workspace 权威源发布 `<target-skill>`。生成投影与远端 checkout 只是只读输出，不能作为可编辑源。

1. 绑定精确源与登记发布器，创建所需 Workspace 写入记录；只有明确授权实际外部写入或推送时才加入 `external_write`。
2. 先生成到获准的 staging 路径，不直接写登记目标。
3. 验证 staging bundle，记录来源 revision，并计算发布器规定的 checksum。
4. 只通过登记发布器写入登记目标。没有外部写入职权时，在验证通过的 dry-run 后停止。
5. 返回审计回执：范围、模式、实际职权、来源 revision、staging 证据、验证/checksum 证据、目标结果，以及停止或下一步条件。

完成条件是源、staging 与目标可追溯；本地验证成功不构成推送许可。
