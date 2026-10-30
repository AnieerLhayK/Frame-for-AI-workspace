# tiktoken 缓存迁移与验证记录

任务：TASK-20261030-012；计划：tiktoken-plan-20261030-001。

已由用户将通用词表缓存从 `${DATA_ROOT}/codex/cache/tiktoken` 独立到共享缓存根下 `${DATA_ROOT}/cache/tiktoken`。采用官方 `TIKTOKEN_CACHE_DIR`，目标为真实目录，不建立软链接。最终结果 PASS，见 apply-result.json 与 verify-result.json；audit.json 和 preflight.json 保留执行前快照。

A001：复制已匹配官方 SHA256 的正式 o200k_base 词表，不复制重复 TMP，保留旧目录。A002：只修改当前用户的该环境变量；已启动应用需重启才继承新值。A003：用全新 staging 隔离环境中的真实 tiktoken 执行断网热缓存加载、中英文往返编码，以及官方 cl100k_base 冷缓存下载与落点验证。不会向现有 Python 环境批量安装包。

原缓存和重复临时文件均保留，未获清理批准。迁移失败时恢复旧环境变量，旧文件仍可用；不自动删除新目录。用户已确认 A001-A003；详见 audit.json 和 plan.json。

代理的 Workspace 写入检查返回 DENY：外部目标不在 cleanup_migration TASK 的可写范围内。代理不直接执行 apply，不修改治理扩权。改由用户以自己的 Windows 权限执行本次固定范围脚本；它只处理本计划的缓存、单一用户环境变量和全新隔离验证目录。

用户已在普通 PowerShell 中执行的命令（一次性迁移，保留供审计）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${WORKSPACE_ROOT}\PROJECT_CONTEXT\reports\tiktoken-relocation-20261030\apply.ps1"
```

脚本在隔离 venv 中安装了固定版本 tiktoken 0.12.0，不修改现有 Python 环境；隔离目录保留，等待单独的清理许可。真实热缓存断网加载、官方 cl100k_base 冷缓存下载、全新进程断网中英文及 emoji 往返编码和原目录未变检查全部通过，apply-result.json 为 PASS。脚本失败时恢复原用户设置；存在目标或 staging 时停止，不自动覆盖，因此成功迁移后不再重复执行 apply。

代理随后独立读回用户环境变量、检查目标的两个词表 SHA256，并在禁止字节码写入的新进程里复跑真实 tiktoken 离线加载及往返编码，结果 PASS。源目录两文件的名称、大小、SHA256 与修改时间仍匹配审计。只读复核以用户注册表的新值配置该验证子进程，没有修改当前 Codex 父进程或其他全局变量。

当前已启动的 Codex 仍继承旧环境值；任务交付后重启应用，让后续进程继承新路径。缓存迁移不代表把 tiktoken 安装进每个 Python 环境。旧缓存和合成验证 staging 均未删除，清理许可与迁移许可分开。
