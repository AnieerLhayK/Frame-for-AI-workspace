# External Knowledge / RAG Planning

> **Evidence Level:** Observed — planning stage, not yet implemented.
>
> This document is a bounded evaluation of whether future external knowledge
> retrieval (RAG, knowledge base, note system) would improve workspace
> maintenance efficiency. It does not implement RAG, create indexes, or
> deploy services.
>
> **Do not use this document as an index or data source.** Use
> `PROJECT_CONTEXT/knowledge_registry.yaml` for current topic routing and
> `PROJECT_CONTEXT/task_registry.yaml` for task resolution.

## Purpose

The workspace has established:

- task routing through `PROJECT_CONTEXT/task_registry.yaml`;
- context budgets through `PROJECT_CONTEXT/context_budget.md`;
- change surface planning through `PROJECT_CONTEXT/change_surface_policy.md`;
- scope verification through `scripts/verify_change_scope.py`;
- knowledge topic discovery through `PROJECT_CONTEXT/knowledge_registry.yaml`;
- workspace engineering methodology through `WORKSPACE_ENGINEERING/`;
- reusable governance, architecture, and anti-pattern records.

Despite these layers, certain recurring pain points remain:

1. Natural-language tasks do not reliably map to the correct task-id on the
   first attempt.
2. Required context sometimes under-covers the actual change surface, leaving
   residual issues.
3. Optional context sometimes over-expands, wasting tokens.
4. Task classification is rule-table based — it lacks semantic fuzziness for
   ambiguous or compound requests.
5. The knowledge registry is a keyword index, not a semantic retrieval layer.
6. Chinese aliases and Chinese retrieval quality are uneven.
7. Maintenance experience, incident post-mortems, task ledger entries, and
   WORKSPACE_ENGINEERING lessons lack a unified retrieval entry point.

This document evaluates whether external RAG / knowledge base / note system
can address these gaps without becoming a competing source of truth.

---

## 一、Current State Assessment

### Task Registry — Strengths

- 32 well-defined task-ids with exact `use_when` conditions.
- Each task declares `required`, `optional`, `ignore`, `write_scope`, and
  `validation` independently.
- The resolver (`scripts/resolve_task_context.py`) routes by exact task-id
  and returns a bounded context view.
- Token budgets are measured per task with `o200k_base` encoding.
- Change surface planning and scope verification catch many misrouted edits.

### Task Registry — Weaknesses

- `use_when` is prose. There is no fuzzy matching against user input.
- Chinese `use_when` descriptions do not exist for most tasks. The
  registry is English-first; Chinese alias coverage is sparse.
- Compound tasks (e.g. "fix drift and update the registry") require
  either two separate resolutions or a manually expanded task.
- There is no fallback when `--list` alone does not suggest the right task.
- The resolver cannot handle "I want to ..." natural language — it needs an
  exact `task-id` or `--list` inspection.

### Knowledge Registry — Strengths

- 20 topics with 66 indexed entries.
- Each entry has a `path`, `layer`, and `purpose` so the reader can decide
  whether to open it.
- Validation passes (20 topics, 66 entries, no errors).
- Topics have Chinese aliases — though quality varies.

### Knowledge Registry — Weaknesses

- Strictly a keyword index — no semantic ranking, no relevance scoring.
- Chinese aliases were hand-added and may be incomplete or misleading.
  For example, "任务管理" maps to `task_and_context_routing`, which is
  correct but narrow. "跨仓写入" maps to `project_boundaries`, which
  is correct but a user searching for "跨仓库写入" would miss it.
- No fuzzy matching or typo tolerance.
- No freshness metadata per entry — the consumer must read the target file
  to know if it is current.
- No cross-language synonym expansion.

### Context Budget — What It Solves

- Prevents broad preloading by defining load levels (A–E).
- Encodes the principle "load the smallest truth-bearing context first."
- Has explicit expansion rules that demand evidence before loading optional
  files.
- Token meter with warning thresholds prevents accidental large reads.
- Works well for routine maintenance (routing + required context only).

### Context Budget — What It Cannot Solve

- It cannot guess what context is missing if the task-id is wrong.
- It cannot prioritize between two plausible required-file sets when the
  task description is ambiguous.
- It does not retroactively detect that a resolved task was the wrong one.
- After reading required context, the agent may still not know what it
  does not know — the budget only limits *how much* is read, not
  *relevance* of what was missed.

### Change Surface Planning & Verification

- `changes plan` compares alternative file sets when there are multiple
  plausible targets.
- `changes verify` catches out-of-scope edits after the fact.
- These are *post-hoc* and *plan-time* correctness checks. They do not
  help at task-selection time.
- They rely on a correct task-id being chosen in the first place.

### Why "Read Too Little" and "Read Too Much" Still Happen

| Problem | Root Cause | Current Mitigation |
|---------|-----------|-------------------|
| Read too little | Wrong task-id chosen | changes verify catches out-of-scope edits after the fact |
| Read too little | Required context correct but agent doesn't know where else to check | Optional context expansion from evidence |
| Read too much | Agent reads broadly because unsure of scope | Context budget Level A→B→C expansion rules |
| Read too much | Task-id too broad for the actual change | Change surface planning for alternative file sets |
| Read stale data | Snapshot report taken as current | Report freshness header + health check |
| Miss Chinese task | Chinese alias missing or incorrect in registry | No mitigation — manual fix required |

---

## 二、是否需要外部 RAG

### Is It Worth Doing?

**Conditionally yes.** External RAG would improve *task discovery* and
*context relevance ranking*, but it is **not urgent** and **not a
replacement** for the existing tooling.

### Problems RAG Fits

1. **Task-id suggestion from natural language.** "I want to add a new
   policy about how agents should handle caching" → suggest
   `shared_policy_update` or `workspace_engineering_knowledge`.
2. **Semantic knowledge retrieval.** "What decisions did we make about
   Hermes guard coverage?" → index across
   `WORKSPACE_ENGINEERING/`, `task_ledger.md`, `current_status.md`,
   `shared/`.
3. **Cross-reference discovery.** "Has the token budget for
   `context_resolution_tooling` been adjusted?" → find references
   across registry, ledger, and status.
4. **Chinese & cross-language retrieval.** "Token 预算怎么配置的" →
   retrieve the context_budget.md regardless of query language.
5. **Stale warning by commit binding.** "This knowledge entry was last
   touched 200 commits ago — verify before use."

### Problems RAG Does NOT Fit

1. **Source of truth.** RAG answers are probabilistic. State,
   protocol, manifest, and Git are deterministic. Never derive
   policy from RAG.
2. **Action execution.** RAG should not suggest edit targets, tool
   commands, or validation steps. Those come from the task registry.
3. **Freshness-critical decisions.** RAG with stale embeddings can
   return deleted paths, old policy, or retired surface rules.
   Only the resolver + manifest + current Git are fresh enough for
   write decisions.
4. **High-cost retrievals on every startup.** Embedding or vector
   lookups add latency and token cost. The existing Level A→B→C
   expansion is cheaper for small tasks.

### Why RAG Must Be Auxiliary Only

- `workspace_manifest.yaml` is the canonical source for paths,
  platform roots, and skill metadata.
- `shared/` protocols are enforceable rules — they should never be
  derived from a similarity search.
- Git state is dynamic. An embedding from yesterday's commit may
  describe a file that was renamed or deleted today.
- RAG databases are write-only snapshots unless maintained.
  Maintenance of the RAG index becomes a new governance burden.
- The existing routing + budget + verify pipeline is deterministic
  and testable. RAG adds a non-deterministic layer that can suggest
  wrong answers without an error trace.

### How To Avoid Stale / Wrong Knowledge In RAG

1. **Commit-bound indexing.** Every RAG entry records the commit hash
   of the source content at index time.
2. **Freshness watermark.** Entries older than N commits (or N days)
   are flagged or excluded.
3. **Source path binding.** Every RAG result includes the source file
   path and commit — never show a generated answer without linking
   to the source.
4. **Separate namespace.** RAG storage lives under
   `${DATA_ROOT}\workspace-rag\` or `${WORKSPACE_ROOT}\knowledge\workspace\`,
   not inside the workspace. The workspace remains the sole
   source of truth.
5. **Validation gate.** Before a RAG-suggested context is loaded,
   the resolver or agent validates that the path still exists and is
   still in the allowed layers.
6. **Never auto-execute.** RAG output is a suggestion to the human
   or agent, never an automatic context load or edit.

---

## 三、工具选型比较

### 1. Obsidian

| Aspect | Assessment |
|--------|-----------|
| Suitability for workspace knowledge | **Strong fit** for human-readable notes, cross-links, maintenance manuals, incident post-mortems |
| Bidirectional links | Excellent for experience capture — link incidents → decisions → policy files |
| Dataview plugin | Could generate tag-based indexes of workspace lessons |
| Canvas | Suitable for architecture diagrams and dependency maps |
| Git compatibility | Vault in `${WORKSPACE_ROOT}\knowledge\workspace\` can be Git-tracked independently |
| Local-only | Works offline, no cloud dependency |
| Query capability | Dataview queries are local and structured, not semantic |
| RAG integration | Obsidian does not natively serve embeddings. Would need a separate retrieval layer on top of its Markdown files |
| Overlap with existing layers | WORKSPACE_ENGINEERING already serves the "reference book" role. Obsidian would duplicate it unless scoped to *unstructured experience capture* that doesn't fit the book structure |

**Verdict:** Obsidian is a good choice for *unstructured experience capture*
(post-mortems, raw design notes, exploratory experiments). It is not a
replacement for WORKSPACE_ENGINEERING (which holds reviewed, structured
methodology). A useful complement but an additional tool to maintain.

### 2. Local Markdown Knowledge Base

| Aspect | Assessment |
|--------|-----------|
| Simplicity | Zero tooling — just Markdown files in a directory |
| Git-manageable | Full history, diff, branching |
| Overlap with PROJECT_CONTEXT | PROJECT_CONTEXT is *active task memory*. A knowledge base should be *long-term reference*. They are distinct roles |
| Overlap with WORKSPACE_ENGINEERING | WORKSPACE_ENGINEERING is already a reviewed reference book. A flat Markdown knowledge base outside the workspace could hold *raw, unreviewed* material that has not been promoted |
| Retrieval quality | Only as good as the directory structure and naming conventions. No search ranking |
| Token cost | Can be read selectively — O(1) to check if a topic exists, then read only matching files |

**Verdict:** Simple and low-risk. Best as P1/P2 staging ground before
deciding to invest in a search layer. Files under
`${DATA_ROOT}\workspace-rag\` can be read by any tool (ripgrep, Claude,
scripts) without needing a database.

### 3. SQLite / DuckDB

| Aspect | Assessment |
|--------|-----------|
| Structured indexing | Excellent for file-path-to-commit mappings, task-to-file mappings, tag cross-references |
| Commit binding | Natural fit — index path, commit_hash, timestamp, content_hash per row |
| Query language | SQL. Deterministic, testable, composable |
| On-disk | Single file, no server, portable |
| Schema evolution | Requires migration discipline |
| Semantic search | Not suitable — no embedding or full-text ranking without FTS5 extension |
| Complexity overhead | Low for SQLite (embedded), moderate for DuckDB (columnar, analytical) |
| Workspace boundary | File lives in `${DATA_ROOT}\workspace-rag\`, not in workspace |

**Verdict:** Best for *structured metadata indexing* — commit bindings,
path-to-task mappings, freshness tracking. Should be considered as a
companion to, not a replacement for, a content search layer.

### 4. Chroma / LanceDB / Qdrant / FAISS

| Aspect | Assessment |
|--------|-----------|
| Semantic search | Strong. Embedding-based similarity finds conceptually related content even when keywords differ |
| Chinese support | Strong with multilingual embedding models |
| Cost / complexity | **High.** Requires embedding model, vector storage, chunking strategy, query pipeline |
| Maintenance burden | Embedding model updates may shift result quality. Database maintenance (compaction, backup) adds operational overhead |
| Deployment | Local only for this use case. No server, but embedding inference still needs a model |
| Freshness | Embeddings from stale content remain high-similarity until rebuilt. Commit binding + freshness watermark mitigate but do not eliminate |
| Workspace fit | The workspace currently has no embedding pipeline. Adding one would be a project of its own |

**Verdict:** **Currently too early.** The workspace has not established
basic text retrieval patterns, let alone embedding infrastructure. If
future experience shows that keyword + BM25 are insufficient, revisit
this category. P4 at earliest.

### 5. ripgrep + BM25 / Whoosh / Tantivy

| Aspect | Assessment |
|--------|-----------|
| Full-text search | ripgrep alone covers fast keyword search. BM25 (Whoosh/Tantivy) adds ranking |
| Chinese support | ripgrep + `-P` (PCRE2) handles Unicode well. BM25 tokenizers vary — Whoosh requires a Chinese tokenizer plugin |
| Simplicity | ripgrep: zero setup. BM25 library: Python package, no server |
| Determinism | Keyword search is deterministic and explainable |
| Cost | CPU and memory only — no embedding inference |
| Integration | Easy to call from Python scripts (subprocess for rg, import for Whoosh) |
| Ranking quality | BM25 is competitive with embedding for many query types, especially when the query contains distinctive terms |
| Workspace fit | ripgrep is already part of the workspace tool ecosystem. Whoosh or Tantivy would be a natural first upgrade |

**Verdict:** **Best first-phase retrieval layer.** ripgrep is already
available. Adding a BM25 index (Whoosh for Python-native, Tantivy
for performance) is the cheapest meaningful upgrade from keyword-only
indexing. P2–P3 candidate.

### 6. Repomix / Repo Map Tools

| Aspect | Assessment |
|--------|-----------|
| Summarization | Can generate a bounded repo summary for a specific subsystem |
| Token saving | A repo map lets the agent understand file relationships without reading all files |
| Offline vs online | Offline snapshot, not live retrieval |
| Freshness | Snapshot is stale from the moment it is generated |
| Workspace fit | The workspace already has `workspace_manifest.yaml` as an explicit map. A repo map would be redundant for most tasks |
| Best use case | Rare. Possibly for onboarding a new agent to an unfamiliar subsystem without any routing context |

**Verdict:** Low priority. The existing routing + registry already serves
the "map" role. Repomix could help when a completely new agent enters
an unknown package, but that is an edge case, not a daily need.

---

## 四、推荐路线

### P0 — Fix Existing Gaps Before Adding RAG

These cost almost nothing and improve the current system directly:

1. **Audit Chinese aliases in `knowledge_registry.yaml`.**
   - Check each topic's `aliases` for missing Chinese variants.
   - Add common Chinese typos / alternative phrasings.
   - Verify that `workspace knowledge find "<中文>"` returns the expected
     topic for at least the 10 most-used topics.

2. **Add `use_when` Chinese summaries to high-traffic task-ids.**
   - Without changing the English prose, add a `use_when_zh` field or
     a comment block for the 10–15 most-used tasks.
   - Target tasks: `project_memory_maintenance`,
     `workspace_engineering_knowledge`, `knowledge_interface_tooling`,
     `context_resolution_tooling`, `change_surface_planning`,
     `change_scope_verification`, `governance_workflow_simplification`,
     `runtime_drift_fix`, `skill_metadata_update`,
     `platform_exposure`.

3. **Add a "task suggest" fallback to `AGENTS.md`.**
   - Instruction: when the user describes a task in natural language and
     `--list` does not produce an obvious match, try:
     ```
     workspace knowledge find "<keywords>"
     grep -r "use_when" PROJECT_CONTEXT/task_registry.yaml
     ```
   - This replaces nothing; it adds a recovery path for ambiguous queries.

**Expected impact:** Reduces wrong-task-id selection by an estimated
20–40% with zero infrastructure cost.

### P1 — External Knowledge Base Planning Document

This document (`WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md`)
serves as the planning baseline. After P0 changes and at least 5–10
real maintenance tasks, revisit this document to:

- Confirm or revise the cost/benefit analysis.
- Add concrete indexing schema sketches (no implementation).
- Decide which external directory path to use.

**No code, no database, no schema at P1.**

### P2 — Define External Directory Structure

Choose one of:

```
Option A: ${DATA_ROOT}\workspace-rag\
  ├── planning/               # This document and future planning artifacts
  ├── indexes/                # Future BM25 / SQLite index files (not yet)
  ├── cache/                  # Transient retrieval cache (not yet)
  └── README.md               # Purpose and governance of this directory
```

```
Option B: ${WORKSPACE_ROOT}\knowledge\workspace\
  ├── planning/
  ├── notes/                  # Raw, unreviewed experience notes
  ├── references/             # Attributed external references
  ├── indexes/
  ├── cache/
  └── README.md
```

**Recommendation:** Option A (`${DATA_ROOT}\workspace-rag\`).
- `${DATA_ROOT}\` already holds workspace data (`claude`, `opencode`,
  `projection-backups`).
- It is already excluded from workspace traversal
  (`task_registry.yaml` → `default_ignore` → `${DATA_ROOT}/`).
- `${WORKSPACE_ROOT}\knowledge\` does not exist yet — creating it is an additional
  decision without clear benefit over reusing `${DATA_ROOT}\`.

### P3 — Design Lightweight Index Prototype (Design Only, No Implementation)

Document the index schema for a future BM25 or SQLite-based system:

- For each source file (from `PROJECT_CONTEXT/knowledge_registry.yaml`,
  `WORKSPACE_ENGINEERING/`, `PROJECT_CONTEXT/`):
  - `path`: workspace-relative path
  - `commit`: commit hash at index time
  - `timestamp`: ISO 8601 index time
  - `content_hash`: SHA-256 of file content at index time
  - `layer`: from knowledge_registry.yaml (or "workspace_engineering")
  - `topics`: array of topic ids from knowledge_registry.yaml

- For task registry entries:
  - `task_id`: exact task-id
  - `use_when`: full English prose
  - `use_when_zh`: Chinese summary (if added in P0)
  - `required_files`: array
  - `write_scope`: array

- Query interface (design only):
  ```
  workspace task suggest "<natural-language query>"
    → candidate task-ids with BM25 score
    → suggested required context
    → optional context
    → risk notes
    → source paths
    → indexed commit
  ```

**Do not implement this in P3.** The schema is recorded for future
evaluation.

### P4 — Plan Future CLI Entry Points

If P2/P3 evaluation is positive, design (do not implement) these
CLI commands as `workspace_cli.py` extensions:

```
workspace task suggest "<自然语言任务>"
  → candidate task ids, ranked
  → suggested required context
  → optional context
  → possible residual files (files the task might need but didn't list)
  → risk notes
  → source paths
  → indexed commit hash

workspace knowledge query "<问题>"
  → matching knowledge_registry entries ranked by relevance
  → BM25 best-guess topics
  → freshness indicator per entry
```

These commands would be read-only. They return information; they do not
load files into context or execute edits. The agent or human still
decides which context to actually load.

### P5 — Define RAG Output Format

When a `task suggest` or `knowledge query` command returns results, the
output should include:

```yaml
candidate_task_ids:
  - task_id: "workspace_engineering_knowledge"
    score: 0.85
    use_when: "Adding, restructuring, validating, or publishing reusable..."
    use_when_zh: "添加或更新可复用的 AI 工作区工程方法论知识"
suggested_required_context:
  - path: "WORKSPACE_ENGINEERING/README.md"
    reason: "Book structure and evidence level rules"
  - path: "WORKSPACE_ENGINEERING/knowledge_provenance.md"
    reason: "External-source attribution rules"
  - path: "PROJECT_CONTEXT/knowledge_registry.yaml"
    reason: "Topic indexing rules"
optional_context:
  - path: "WORKSPACE_ENGINEERING/architecture_patterns.md"
    reason: "Reusable structure patterns — may be relevant"
freshness:
  indexed_commit: "abc123def"
  source_still_exists: true
  commits_since_index: 42
  stale: true   # if > threshold
risk_notes:
  - "This task has a broad write_scope. Use changes plan to narrow."
```

### P6 — Freshness / Commit Binding / Stale Warning Mechanism

Design (do not implement):

1. **Index-time binding.**
   - Every indexed file records `git rev-parse HEAD` at index time.
   - Every indexed file records its `content_hash` (SHA-256).

2. **Query-time freshness check.**
   - Before returning a result, check `git log -1 --format=%H <path>`.
   - If current commit differs from indexed commit → `stale: true`.
   - If file no longer exists → `stale: true`, `deleted: true`.

3. **Stale threshold.**
   - `commits_since_index > 10` → stale warning.
   - `days_since_index > 30` → stale warning.
   - Either condition → result is flagged, not excluded.

4. **Auto-rebuild trigger (future).**
   - Not implemented in P0–P5.
   - Potential trigger: post-commit hook or daily cron.
   - Must not write to the workspace.

---

## 五、Proposed File Changes

### Files To Create

| File | Purpose |
|------|---------|
| `WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md` | This planning document |

### Files To Update

| File | Change |
|------|--------|
| `PROJECT_CONTEXT/knowledge_registry.yaml` | Add topic for `external_knowledge_planning` |
| `PROJECT_CONTEXT/todo/workspace-optimization.md` | Add P2 entry for external knowledge evaluation |
| `PROJECT_CONTEXT/task_ledger.md` | Record this planning task |
| `PROJECT_CONTEXT/current_status.md` | Add note that RAG planning is in evaluation |
| `WORKSPACE_ENGINEERING/README.md` | Add `external_knowledge/` to book structure |

### Files NOT To Touch

- `scripts/` — no implementation work this round.
- `shared/` — no policy change.
- `.claude/` — no boundary change.
- `USAGE_GUIDES/` — no user-facing change until P4.
- Existing `WORKSPACE_ENGINEERING/` files are read, not rewritten.

---

## 六、规划结论

### 1. 是否推荐现在做 RAG？

**不推荐现在做完整 RAG。** 建议先做 P0（中文 alias 优化 + use_when_zh
补充 + task suggest 兜底指令），观察 5–10 个真实任务后重新评估。

完整向量 RAG 的引入条件：

- P0 做完后 wrong-task-id 的比率没有明显下降；
- 自然语言→task-id 映射的需求仍然频繁出现；
- 当前 keyword index 确实不够用（由真实失败案例证明，不是理论推测）。

### 2. 如果推荐，先做什么？

当前阶段的推荐顺序：

```
P0: 中文 alias 修补 + use_when_zh 补充 (零成本, 立刻生效)
↓
P1: 外部知识库规划文档 (本文)
↓
P2: 目录结构落地 ${DATA_ROOT}\workspace-rag\ (需手动创建 README)
↓
P3: BM25 轻量原型设计 (Whoosh, 仅设计不实现)
↓
P4: CLI 入口设计 (仅设计不实现)
↓
P5: 评估是否转向向量 RAG (Chroma/LanceDB)
```

### 3. 哪些内容应该留在 workspace？

**所有确定性内容**必须留在 workspace：

- `workspace_manifest.yaml` — canonical path registry
- `shared/` — enforceable protocols
- `PROJECT_CONTEXT/task_registry.yaml` — task routing
- `PROJECT_CONTEXT/context_budget.md` — context policy
- `PROJECT_CONTEXT/knowledge_registry.yaml` — topic index
- `WORKSPACE_ENGINEERING/` — reviewed methodology
- `AGENTS.md` — startup instructions
- Git current state — dynamic source truth
- `scripts/` — tool implementations

### 4. 哪些内容应该放到 ${DATA_ROOT} 或 ${WORKSPACE_ROOT}\knowledge？

**非确定性、辅助性、未review的内容**放到外部目录：

- RAG index files (BM25/SQLite/vector)
- Raw, unreviewed experience notes (before promotion to
  WORKSPACE_ENGINEERING)
- External reference copies or attributed snippets (before provenance
  review)
- Transient retrieval cache (to avoid re-indexing every query)
- Planning artifacts that are not workspace methodology

### 5. 如何避免 workspace 被知识库污染？

| Rule | How |
|------|-----|
| Never write RAG data into workspace. | External directory lives under `${DATA_ROOT}\`. |
| Never import RAG as a truth source. | Always resolve through `task_registry.yaml` first. |
| RAG output is suggestion, not command. | CLI commands are read-only. Agent still validates paths exist. |
| Git is the boundary. | Workspace is Git-tracked. External directory is not part of the workspace repo. |
| `default_ignore` already excludes `${DATA_ROOT}/`. | `task_registry.yaml` line 129. RAG directory is covered. |
| No symlinks or junctions from workspace to RAG directory. | Enforce during P2 directory creation. |

### 6. 如何证明未来方案真的节省 token？

Measure before and after:

| Metric | Before (current) | After (with RAG) |
|--------|-----------------|------------------|
| Wrong task-id resolution rate | Log current | Compare after P0 |
| Average context loaded per task | `resolve_task_context.py` token meter | Same meter after P4 |
| "Read too little" incidents per 10 tasks | Subjective log | Subjective log |
| "Read too much" incidents per 10 tasks | Subjective log | Subjective log |
| Time to find correct task-id | Human judgement | Compare after P0 |

Token savings should be measured empirically (using the existing
`o200k_base` meter), not estimated theoretically.

### 7. 如何避免治理机制继续膨胀？

- RAG remains a **read-only suggestion layer**, not a governance mechanism.
- No new validation gates depend on RAG output.
- RAG does not create new `write_scope`, `required`, or `validation`
  entries in the task registry.
- If P0 addresses 80 % of task-id confusion, stop at P0. Do not build
  P3–P5 unless the remaining 20 % causes real friction.
- **Governance rule:** a new external retrieval mechanism must remove or
  simplify an existing mechanism, not stack on top of it.

### 8. 下一步最小可行动作是什么？

1. **审计 `knowledge_registry.yaml` 的中文 alias**，补充缺失的中文
   variant（~30分钟）。
2. **为 10–15 个高频 task-id 添加 `use_when_zh` 注释**（~20分钟）。
3. **在 `AGENTS.md` 中添加 task suggest 兜底指令**（~5分钟）。
4. **在 `PROJECT_CONTEXT/todo/workspace-optimization.md` 中添加 P2: 外部知识库评估**。
5. **完成以上 P0 步骤后，标记本文为 `Validated locally` 状态。**

---

## Appendix: Task-ids And Their `use_when_zh` Candidates

(The top 15 most-used task-ids that would benefit from Chinese
`use_when` summaries. Edit `task_registry.yaml` to add these.)

| task-id | use_when_zh candidate |
|---------|----------------------|
| `project_memory_maintenance` | 更新当前状态、待办、交接记录或已完成任务元数据，不改变工作区行为 |
| `workspace_engineering_knowledge` | 添加、重构或验证可复用的 AI 工作区工程方法论知识 |
| `knowledge_interface_tooling` | 修改知识注册表或只读主题发现接口 |
| `context_resolution_tooling` | 修改任务上下文解析器、Token 计量、预算阈值或注册表解析合约 |
| `change_surface_planning` | 修改比较多个候选文件集的只读规划工具 |
| `change_scope_verification` | 修改对比实际 Git 变更与任务 write_scope 的只读验证工具 |
| `governance_workflow_simplification` | 统一变更风险分类或简化日常维护工作流 |
| `runtime_drift_fix` | 诊断或修复运行时角色风格漂移 |
| `skill_metadata_update` | 修正 SKILL.md 的发现元数据或 frontmatter |
| `platform_exposure` | 修复 Codex/Claude Code/OpenCode/Hermes 的技能加载路径 |
| `startup_context_optimization` | 减少始终加载的 Agent 指令或启动上下文 |
| `task_registry_update` | 修改任务路由、上下文边界或任务分类规则 |
| `developer_interface_tooling` | 修改统一工作区 CLI 或其命令委派逻辑 |
| `report_regeneration` | 在源文件、协议或链接变更后重新生成快照报告 |
| `shared_policy_update` | 添加或修改可选的共享策略（不成为始终加载的规则） |
