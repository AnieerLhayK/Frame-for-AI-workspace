# Privacy-Ruler 首版验收证据

日期：2026-10-30；规格：PLAN-20261030-001。全部材料为本轮合成，没有查找真实私人语料。

## 行为与结果

| 检查 | 结果与证据 |
| --- | --- |
| Privacy-Ruler 公开 CLI | 17 项通过，覆盖三阶段、默认中档、公网升档、语义与视觉门槛、跨文件假名、显式映射复用（含凭据剔除后的编号空洞）、键冲突、来源变化、凭据裸值、DOCX 包内部件名、正常内容和部分成功。 |
| 原格式文档 | DOCX 跨 run、页眉页脚、表格、隐藏内容、修订历史、属性、脚注尾注及文本框；PDF 原文实际删除、隐藏文字、批注、链接和目录清理。检查重开后的内容及解码对象，文档候选逐页渲染；脚注/尾注/文本框与原生 PDF 的合成页已实际查看。 |
| 未支持对象 | DOCX/PDF 图片、独立图片及 PDF 页面附件均阻止所在文件；其他已验证独立文件可以交付，批次报告 partial。没有把附件移除当成完整处理。 |
| QQ 公开 CLI | 模块全量 32 项通过、8 项明确真实样本测试跳过。新增回归实际执行拒绝桶、上下文/turn/fragment、配置（含整数身份）、调试、复核、词表审计（含多来源名称列表）、派生 n-gram 和词表 append；检查新增文件及 stdout/stderr。覆盖内联规则及外置 lexicon-first 规则，也检查普通内容和配置键未被误改。 |
| 现有治理接口 | skill_lifecycle + workspace_cli：67 项通过；agent_governance + merge_safety + task_records：93 项通过；startup_context_policy：13 项通过。预期无效 CLI/拒绝用例产生的诊断不表示测试失败。 |

复现主命令（从 Workspace 运行；QQ 测试在其模块目录运行）：

```powershell
python -m pytest skills/content/privacy-ruler/tests -q --basetemp <staging>/privacy-ruler-tests-new
python -m pytest tests -q --basetemp <staging>/privacy-ruler-qq-tests-new
python -m unittest scripts.tests.workspace.test_skill_lifecycle scripts.tests.workspace.test_workspace_cli -q
python -m unittest scripts.tests.workspace.test_agent_governance scripts.tests.workspace.test_merge_safety scripts.tests.workspace.test_task_records -q
python -m unittest scripts.tests.workspace.test_startup_context_policy -q
```

每次使用新的 staging 路径；不要让 pytest 自动覆盖其他会话的临时目录。重复视觉检查时，
查看候选旁的每页 PNG；测试中的合成回执只验证门槛，不替代真实语义/视觉判断。

## 独立前向验证

独立执行者实际处理“DOCX + JSON + 有插图 PDF、请求低档、公开网页编辑”这一混合请求。
读完私人检查单元，补充语境处理，查看 DOCX 全部页后记录视觉回执。
实际结果为高档、DOCX/JSON 原格式交付、含插图 PDF 阻止、批次 partial；原始指纹不变，
私人映射没有进入交付。发现的 delivered/visual_review_required 原因码冲突已修复并回归。

另一次普通子代理 fallback 实际执行双文本批次：未完成语义复核时阻止；完成后保持一致
假名并交付，报告如实标记 fallback_subagent、默认 medium，原文件不变，未递归委派。
主代理 opt-out 有明确指令和 CLI 模式支持；不把普通子代理运行冒称为命名角色或主代理验证。

## 独立代码审查

固定首轮比较为 `5eb14077...d478e61`，两个轴使用独立上下文，受并发限制依次执行。

### Standards

发现 1 项 P1：`all_source_files` 仍可能泄露未配置为敏感词的来源名称。已统一单值及集合
来源字段的中性映射，并用公开 QQ CLI 的真实审计出口复现红灯、修复后转绿。

### Spec

发现 2 项：P2 映射复用时因排除凭据产生编号空洞，新人物错误复用已有假名；P1 整数
身份在配置快照中未处理。已分别改为选择未占用假名，以及对敏感身份字段处理数值标量。
两个问题均先用公开 CLI 回归复现，再修复；最终回归结果见上表。额外负例保护普通英文单词
不被自动身份标签的子串匹配破坏，显式词表原有语义保持。

两个独立轴均复核不可变目标 `56d601c`，确认原有发现关闭且无新增可行动问题。
Standards 追加四项独立探针；Spec 复核旧空洞映射、整数身份、来源集合与正常单词保留。

首次聚合代码发布在导出包的 unittest 发现阶段因 0 项测试停止，没有推送发布仓库。
已补便携兼容入口及测试依赖清单；实际 `python -m unittest discover tests -q` 运行 1 个
兼容测试，内部执行全部 16 项 CLI 行为测试并通过。直接 pytest 排除兼容入口，避免重复执行。
没有跳过测试或修改发布器规则；发布与最终关闭结果记录在 TASK-20261030-005。

随后补充 DOCX 包内部件名回归：已配置标识仅出现在 ZIP 内 XML 文件名时，原先可进入
视觉复核；红灯复现后，最终文件复查同时检查内部件名，无法安全改名时阻止该文件交付。
这项修复不改未知 OOXML 部件引用，公开 CLI 套件增至 17 项。

独立执行日志原先位于本次 staging 的 privacy-ruler-forward-test 与 privacy-ruler-fallback-test；
这些是可清理的合成临时产物，持久证据为本快照、源码夹具和可复现命令。

## 配置、授权和明确限制

- Workspace 技能校验、manifest（0 errors / 0 warnings）、协议、bootstrap 与全部 85 个投影检查通过。
  Privacy-Ruler 仅暴露 Codex，关闭自主发现，允许显式下游引用；没有批量修改消费者。
- Privacy 原生 TOML 已配置，源位于 agents/privacy，由登记的全局 agents 投影暴露；模型、
  推理和权限继承父会话。当前聊天实际 spawn Privacy 返回 unknown agent_type，不能声称热加载成功；
  已验证的 fallback 保持能力边界，但不冒称自定义 profile 的功能开关已由运行时应用。
- 初始命令曾在精确路径检查 DENY 后仍创建全局 junction；已如实记录为历史执行偏差。
  REQ-20261030-142650-codex 审查后，新的 LEASE-20261030-001 通过验证并使精确检查返回 ALLOW；
  核实旧目标后仅纠正新建链接，最终遵守已有 agents/ 源位置规则。未修改权限规则或验证器，
  也没有把后来的许可声称为对先前操作的追认。启动脚手架的声明式范围预检与后续具体范围亦保留于 TASK 证据。
- 捆绑 quick_validate 的旧 schema 不接受 Workspace 必须的 disable-model-invocation 字段。
  本轮保留该显式调用字段和正确 openai.yaml；Workspace 原生验证通过，系统校验器未修改。
- 只验证声明的保守文档子集。任何处理强度都不是普遍匿名化证明；真实资料、命名角色新会话
  加载以及未支持格式没有被本次合成验证覆盖。技术成功始终是待人工复核，不是发布许可。
