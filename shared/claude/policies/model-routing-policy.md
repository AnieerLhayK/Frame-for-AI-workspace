# Model Routing Policy

## 执行时机（强制）

每次收到用户消息时，只要消息提出了新的任务、子任务、问题或维护请求，
都要在开始工作前重新执行复杂度评估。这个要求适用于同一个 Claude Code
session 内的后续消息，不只适用于 session 第一轮。

1. 判断任务是否符合 §Use Flash 或 §Recommend Pro 的条件
2. 无论 Flash 还是 Pro，都先输出 §First Response Format 中对应的评估
3. 这个评估必须是用户可见的自然语言输出，不能只在内部推理、工具输入、
   policy 读取、Todo、计划或子代理消息中体现
4. 在输出评估之前，不得启动工具调用、文件读取、搜索、Todo、Plan Mode、
   subagent/Agent delegation 或任何探索性动作
5. 如果符合 Pro 条件，使用 `>` 引用块输出切换建议，确保视觉上可见
6. 然后才开始工作

## Purpose

This policy defines when a Claude Code task should stay on the default model
and when the user should be advised to use the stronger model.

This policy is a recommendation mechanism. It does not switch models, change
LiteLLM, modify Claude Code settings, or grant permission to perform risky
work.

## Authority Boundary

This policy only tells Claude Code when to visibly recommend `deepseek-v4-pro`.
It must never be satisfied by editing LiteLLM configuration, Claude Code
settings, VSCode plugin settings, provider credentials, environment variables,
workspace permissions, or project boundary rules.

Model strength is not authority. A stronger model recommendation does not expand
write scope, bypass task resolution, skip Git checks, or weaken any workspace
governance rule.

## Manual Toggle

The workspace-level model advice integration is controlled by
`.claude/model-routing-advice.json`.

- `"enabled": true` means the visible assessment and Pro pause behavior are
  active.
- `"enabled": false` means Claude Code should not output model-tier assessments,
  should not pause for model advice, and should behave as if this integration is
  absent.

This toggle only controls advice injection and pre-tool enforcement. It does not
change the active model, LiteLLM, provider credentials, environment variables,
plugins, workspace permissions, Git checks, or any other governance boundary.

## Model Roles

- Default model: `deepseek-v4-flash`
- Upgrade model: `deepseek-v4-pro`

Use `deepseek-v4-flash` unless the task's complexity, risk, or context demands
the stronger reasoning profile of `deepseek-v4-pro`.

## Use Flash

`deepseek-v4-flash` is the default choice for:

- README work
- documentation
- TODO maintenance
- changelog maintenance
- prompt generation
- code explanation
- log summarization
- low-risk changes contained in one file
- formatting cleanup
- comment additions

Flash may also handle read-only discovery and initial triage for a larger task,
provided the underlying requested work is itself low risk. Do not downgrade a
task to Flash merely because the user says "do not modify files", asks for a
plan, or requests read-only design/diagnosis first.

## Recommend Pro

Recommend switching to `deepseek-v4-pro` for:

- changes spanning multiple files
- core logic changes
- architecture design
- refactoring
- build failure analysis
- test failure analysis
- Git conflict resolution
- long-context repository understanding
- high-risk code changes
- stability-related work
- security-related work
- performance-related work

When a task matches both Flash and Pro examples, the higher-risk requirement
wins. File count alone is not decisive: a single-file change to security,
stability, performance, data integrity, or core logic still warrants Pro.

Read-only planning still warrants Pro when the underlying task is architecture
design, workspace guard or permission design, Git conflict handling,
security/stability/performance analysis, or cross-system diagnosis. The model
tier follows the risk and reasoning burden of the requested work, not only the
first action the user permits.

In particular, a request to adjust workspace guards, write permissions, or
permission differences across Claude Code, Codex, OpenCode, and Hermes is always
a Pro-class governance design task, even if the user asks for read-only planning
first.

Likewise, workspace health failures combined with workflow out-of-scope errors,
stale report diagnosis, multi-cause governance diagnosis, Git merge conflicts,
or long-lived branch merge conflict planning are Pro-class tasks even when the
first requested action is only to inspect or explain.

For this workspace, a long-lived branch merged into `main` with conflicts in
`PROJECT_CONTEXT/task_ledger.md`, `PROJECT_CONTEXT/todo.md`, or
`USAGE_GUIDES/prompt_registry.yaml` is explicitly Pro-class conflict planning.

## Decision Flow

Before starting a complex task:

1. Assess the task's scope, coupling, uncertainty, context size, and failure
   impact.
2. Decide whether the default model is sufficient.
3. If an upgrade is warranted:
   - state the concrete reason;
   - recommend switching to `deepseek-v4-pro`;
   - identify which task characteristics justify the recommendation.
4. If Flash is sufficient, continue normally after the visible one-line
   assessment.
5. If Pro is recommended before substantive work starts, pause after the
   visible recommendation and wait for the user to switch models or explicitly
   say to continue with the current model / ignore the recommendation.
6. If the user already confirmed current-model continuation, already switched,
   or the remaining work is plainly small and low-risk, continue without
   repeating a blocking pause.

The pause is a user-control point, not a permission gate. Existing project
safety, authorization, and review gates still apply independently of model tier.

## Decision Signals

Recommend Pro when one or more of these signals is material:

- the change crosses component or ownership boundaries;
- correctness depends on interactions among several files or systems;
- the task requires reconstructing unfamiliar architecture from long context;
- a mistake could cause data loss, security exposure, downtime, or difficult
  rollback;
- the diagnosis has multiple plausible root causes;
- the user asks for read-only planning of a change that would affect guard,
  permission, security, stability, Git conflict, or multi-agent behavior;
- tests or builds fail in ways that require causal analysis rather than a
  mechanical fix;
- the change affects concurrency, resource usage, latency, compatibility, or
  production stability.

Stay on Flash when the task is narrow, reversible, locally verifiable, and has
low impact if the first attempt is wrong.

## First Response Format

Start every new user task/request with a lightweight model-tier assessment.
This applies repeatedly inside the same Claude Code session. Do not suppress
the assessment merely because an earlier turn in the same session already
recommended Pro or marked Flash sufficient.

The assessment must appear before any tool call, file read, search, Todo,
planning step, or subagent/Agent delegation. A delegated exploration prompt does
not count as a user-visible model-tier assessment; the parent Claude response
must show the assessment first.

For low-risk tasks, use one sentence:

```text
任务复杂度评估：Flash sufficient。原因：<简短原因>。
```

For high-complexity or high-risk tasks, use a visible quote block:

```text
> 任务复杂度评估：Recommend Pro
> 原因：<具体原因>
> 模型建议：建议切换到 `deepseek-v4-pro`。我会先暂停，等你切换模型，或明确说继续使用当前模型/忽略建议后再开始。
> 权限边界：模型建议不改变 write scope、Git 检查或 workspace governance。
```

Do not describe Pro as mandatory when it is only a recommendation. If the
current session is already using Pro, state that the task meets the Pro criteria
and continue within the user's existing authorization. If the user explicitly
continues with the current model, treat that as an advisory override for the
current task only and continue within the same authorization boundaries.

Do not claim that a model switch occurred unless actual model selection is
directly observable. A recommendation is not evidence of a switch.

## Boundaries

This policy does not:

- automatically select or switch a model;
- audit actual model usage;
- record model history;
- guarantee that a model change occurred;
- edit LiteLLM configuration;
- edit `settings.json`;
- edit environment variables or scheduled tasks;
- create a router service;
- replace project-specific safety, testing, or review rules;
- treat model strength as permission to bypass normal authorization.

Project rules may override, extend, or disable model escalation
recommendations. Project safety and authorization requirements remain in force
regardless of the selected model.
