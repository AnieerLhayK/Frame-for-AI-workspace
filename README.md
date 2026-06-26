# Agent Ecosystem Workspace

This workspace is governed by `workspace_manifest.yaml` as the source of truth for skill roots, roles, authority, execution modes, shared protocols, and platform exposures.

## Project Context

New human or agent sessions should start with `ARCHITECTURE.md`, then read `PROJECT_CONTEXT/README.md`, `PROJECT_CONTEXT/current_status.md`, and `PROJECT_CONTEXT/todo.md`.

`PROJECT_CONTEXT/` is the active task memory layer (task ledger, registry, status, todo). It orients current work but does not replace `workspace_manifest.yaml`, `ARCHITECTURE.md`, `shared/`, `reports/`, or `packages/character-system/reports/runtime-loop/`.

This workspace is a governed skill monorepo, not a single giant agent. Before adding a new skill, decide whether it belongs in an existing package/domain, a new package/domain, a standalone skill area, or a separate workspace. Do not force unrelated business rules into top-level `shared/`.

Platform loading is not capability ownership. The same source skill may be exposed to more than one compatible platform without changing its role or authority.

## Claude Code Project Boundary

Claude Code uses its startup directory as the project root. This workspace is
registered through root `CLAUDE.md` and tracked `.claude/` rules as a governed
skill workspace; it is not a container for unrelated business projects.

Use the explicit launchers:

```powershell
claude-workspace
claude-cnn
claude-ztemp
claude-project <alias>
```

You can also run `claude` directly after changing into the intended Git root.
Do not change repositories inside an already-running Claude session; restart it
from the target repository so native editing tools load the correct guard.

The CNN repository is a separate Git project selected by the machine-local
Claude project registry. It is intentionally not registered in
`workspace_manifest.yaml`, because that manifest governs workspace skills and
platform projections rather than external Claude Code projects.

## Skill Engineering Knowledge

`WORKSPACE_ENGINEERING/` is the reusable AI workspace engineering knowledge
base. It covers architecture, Agent governance, portability, task/context
routing, operational lessons, and Skill Engineering as a subdomain. It is not
current project status and it is not an enforceable protocol layer.

Use `PROJECT_CONTEXT/` to understand this workspace now. Use
`WORKSPACE_ENGINEERING/` when designing future workspaces, Skills, Agent
governance, or reusable maintenance patterns.

## Usage Guides

`USAGE_GUIDES/` is the prompt-first usage layer. Open it when you want
copy-ready prompts, role-oriented skill references, and platform-specific
loading instructions.

## Minimum Maintenance Workflow

Use this baseline for future maintenance:

1. Check `git status --short`.
2. List task ids with `python scripts/resolve_task_context.py --list` when needed.
3. Resolve the task with `python scripts/resolve_task_context.py <task-id>`.
4. Read only the returned required context.
5. Edit the narrowest owning layer.
6. Run the returned validation commands.
7. Update PROJECT_CONTEXT when long-term decisions, risks, or next steps change.
8. Wait for explicit confirmation before committing unless the user asked for a commit.

## Context Resolver

The resolver joins the task registry, prompt registry, and token budget without writing files:

```powershell
python scripts\resolve_task_context.py --list
python scripts\resolve_task_context.py --list-prompts
python scripts\resolve_task_context.py platform_exposure
python scripts\resolve_task_context.py skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\resolve_task_context.py runtime_drift_fix --bind target-character=packages/character-system/runtime/characters/zyc --include-optional
python scripts\resolve_task_context.py --prompt-id zyc_natural_discussion --include-template
```

Direct prompt resolution extracts only the requested Markdown section when a registry path contains an anchor. Use `--format json` for agent or script integration. Install `scripts/requirements-context-tools.txt` for exact `o200k_base` token counts; otherwise the resolver uses a clearly marked heuristic.

The unified developer CLI is a thin entry point over the existing resolver and workspace tools:

```powershell
python scripts\workspace_cli.py task list
python scripts\workspace_cli.py task resolve platform_exposure
python scripts\workspace_cli.py prompt list
python scripts\workspace_cli.py prompt show task_routing --format json
python scripts\workspace_cli.py preflight skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py bootstrap --print-json
python scripts\workspace_cli.py health
python scripts\workspace_cli.py health --with-tests
python scripts\workspace_cli.py summary
python scripts\workspace_cli.py summary --format json
python scripts\workspace_cli.py sessions audit
python scripts\workspace_cli.py sessions audit --migration-id character-package-20260614 --format json
python scripts\workspace_cli.py agent status
python scripts\workspace_cli.py agent check --agent hermes --path workspace_manifest.yaml
python scripts\workspace_cli.py agent request --agent hermes --mode review_only --summary "Register a missing skill" --path workspace_manifest.yaml
python scripts\workspace_cli.py skill list
python scripts\workspace_cli.py skill validate character-generator
python scripts\workspace_cli.py skill expose character-generator --platform codex
python scripts\workspace_cli.py launcher install
python scripts\workspace_cli.py failure check skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py validate links
python scripts\workspace_cli.py reports status
python scripts\workspace_cli.py reports status --strict --format json
python scripts\workspace_cli.py reports refresh workspace
python scripts\workspace_cli.py changes plan developer_interface_tooling --intent tooling
python scripts\workspace_cli.py changes plan skill_metadata_update --intent metadata --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py knowledge list
python scripts\workspace_cli.py knowledge validate
python scripts\workspace_cli.py knowledge find "skill 开发"
python scripts\workspace_cli.py knowledge find "工程现状" --layer project_context
```

`preflight` uses strict token-budget enforcement. `reports status` and `validate links` are read-only. Report refresh is explicit; `validate manifest`, `validate protocols`, and `reports refresh` retain the existing generators' snapshot-writing behavior.

`sessions audit` is also read-only. It verifies that manifest-declared Claude
Code and OpenCode stores, migration backups, portable exports, and recorded
session IDs are still recoverable after source paths move.

Change-surface planning is also read-only. It ranks the resolved task's writable
layers by explicit intent. To compare concrete alternatives, repeat
`--option NAME=PATH1,PATH2`; options outside the resolved write scope, projection
paths, and report-only substitutes are blocked before ranking.

Knowledge lookup is registry-backed and read-only. It returns entry paths and
purposes without searching or loading every indexed file. The registry is a
routing index; manifest, shared policy, source files, and current Git state retain
their existing authority.

Agent governance is policy-backed. It distinguishes skill invocation from
workspace modification, classifies target paths, and routes denied structural
work into reviewable requests. It does not authenticate agent identity or
automatically issue leases, create worktrees, merge branches, or edit platform
registries.

Resource enforcement follows `workspace_manifest.yaml -> failure_policy`:

- missing required or preloaded context returns overall status `ERROR` and exit code `1`;
- missing optional context is reported as `WARNING` only when optional context is expanded;
- JSON output exposes `context.resource_findings`, overall `status`, and the separate `token_budget.budget_status`;
- unresolved required, write-scope, or validation placeholders stop resolution instead of triggering path guesses.

Startup-context regression checks:

```powershell
python -m unittest scripts.tests.test_startup_context_policy
```

## Shared Protocol Validation

The character-system protocol layer is registered in `packages/character-system/shared/protocol_manifest.json`.

Run this check after changing `shared/`, runtime-loop templates, ledgers, or any core skill `SHARED_PROTOCOLS.md` file:

```powershell
python scripts\validate_protocols.py
```

The validator writes `reports/protocol_validation_report.md`. That report is a snapshot; the truth sources remain `workspace_manifest.yaml`, `packages/character-system/shared/protocol_manifest.json`, `shared/`, and current Git state.

## Portability Checks

Workspace discovery is bounded. Tools should find `workspace_manifest.yaml` by walking upward from a known start path, never by scanning a whole drive.

Before moving the workspace, shared root, platform projection roots, or drive letter, run:

```powershell
python scripts\bootstrap_workspace.py
python scripts\validate_manifest.py
python scripts\migration_dry_run.py --scenario root-rename --new-root <new-workspace-root>
python scripts\validate_protocols.py
powershell -ExecutionPolicy Bypass -File scripts\check_links.ps1
```

Platform projection roots may remain absolute because they are local deployment entry points. Workspace-internal source paths should stay workspace-relative when possible.

## Continuous Integration

GitHub Actions runs the basic Python CI workflow on every push and pull request,
and it can also be started manually from the Actions tab.

The workflow installs the repository's Python tooling dependencies, compiles the
Python source directories to catch syntax errors, and runs all tests
discovered by `pytest`, including the suites under `scripts/tests/` and
`packages/character-system/engineering/generation/character-generator/tests/`.

When CI fails, open the failed run in the repository's Actions tab, select the
`python-quality` job, and expand the failed step to view the command output and
traceback.
