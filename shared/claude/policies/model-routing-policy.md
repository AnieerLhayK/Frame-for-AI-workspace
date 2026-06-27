# Model Routing Policy

## 执行时机（强制）

每次收到新任务时，在开始工作前先执行复杂度评估：

1. 判断任务是否符合 §Use Flash 或 §Recommend Pro 的条件
2. 如果符合 Pro 条件，在第一次回复中使用 `>` 引用块输出切换建议，确保视觉上可见
3. 然后才开始工作

## Purpose

This policy defines when a Claude Code task should stay on the default model
and when the user should be advised to use the stronger model.

This policy is a recommendation mechanism. It does not switch models, change
LiteLLM, modify Claude Code settings, or grant permission to perform risky
work.

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
provided it does not proceed into high-risk modification.

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

## Decision Flow

Before starting a complex task:

1. Assess the task's scope, coupling, uncertainty, context size, and failure
   impact.
2. Decide whether the default model is sufficient.
3. If an upgrade is warranted:
   - state the concrete reason;
   - recommend switching to `deepseek-v4-pro`;
   - identify which task characteristics justify the recommendation.
4. Continue working normally unless the user chooses to switch models.

Do not block work, interrupt the task solely for model-tier considerations, or
require model-switch approval before continuing. Existing project safety,
authorization, and review gates still apply independently of model tier.

## Decision Signals

Recommend Pro when one or more of these signals is material:

- the change crosses component or ownership boundaries;
- correctness depends on interactions among several files or systems;
- the task requires reconstructing unfamiliar architecture from long context;
- a mistake could cause data loss, security exposure, downtime, or difficult
  rollback;
- the diagnosis has multiple plausible root causes;
- tests or builds fail in ways that require causal analysis rather than a
  mechanical fix;
- the change affects concurrency, resource usage, latency, compatibility, or
  production stability.

Stay on Flash when the task is narrow, reversible, locally verifiable, and has
low impact if the first attempt is wrong.

## Upgrade Message

Use a concise message in this form:

> ⚠ 建议切换模型：此任务符合 `deepseek-v4-pro` 的使用条件，因为 <具体原因>。我继续使用当前模型工作，由你决定是否切换。

Do not describe an upgrade as mandatory when it is only a recommendation. If
the current session is already using Pro, state that the task meets the Pro
criteria and continue within the user's existing authorization.

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
