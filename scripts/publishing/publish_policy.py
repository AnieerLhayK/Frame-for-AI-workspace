"""Public projection selection and machine-path scrubbing policy."""
from __future__ import annotations
import re

SUBSTITUTIONS: list[tuple[re.Pattern[str], str]] = [
    # Windows backslash paths
    (re.escape(r"${OTHER_PROJECT_ROOT}/source/repos/CNN"),
     "${OTHER_PROJECT_ROOT}/source/repos/CNN"),
    (re.escape(r"${DATA_ROOT}/workspace-governance"),
     "${DATA_ROOT}/workspace-governance"),
    (re.escape(r"${DATA_ROOT}/hermes"),
     "${DATA_ROOT}/hermes"),
    (re.escape(r"${DATA_ROOT}/codex"),
     "${DATA_ROOT}/codex"),
    (re.escape(r"${DATA_ROOT}/claude"),
     "${DATA_ROOT}/claude"),
    (re.escape(r"${DATA_ROOT}/opencode"),
     "${DATA_ROOT}/opencode"),
    (re.escape(r"${DATA_ROOT}/reasonix"),
     "${DATA_ROOT}/reasonix"),
    (re.escape(r"${DATA_ROOT}/out/workspace"),
     "${DATA_ROOT}/out/workspace"),
    (re.escape(r"${DATA_ROOT}/out"),
     "${DATA_ROOT}/out"),
    (re.escape(r"${DATA_ROOT}/playwright-mcp"),
     "${DATA_ROOT}/playwright-mcp"),
    (re.escape(r"${DATA_ROOT}/playwright-browsers"),
     "${DATA_ROOT}/playwright-browsers"),
    (re.escape(r"${DATA_ROOT}"),
     "${DATA_ROOT}"),
    (re.escape(r"${WORKSPACE_ROOT}"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"${WORKSPACE_ROOT}"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"${DEV_ROOT}"),
     "${DEV_ROOT}"),
    (re.escape(r"${SCRATCH_ROOT}"),
     "${SCRATCH_ROOT}"),
    # Forward-slash variants
    (re.escape(r"${DATA_ROOT}/workspace-governance"),
     "${DATA_ROOT}/workspace-governance"),
    (re.escape(r"${DATA_ROOT}/hermes"),
     "${DATA_ROOT}/hermes"),
    (re.escape(r"${DATA_ROOT}/codex"),
     "${DATA_ROOT}/codex"),
    (re.escape(r"${DATA_ROOT}/claude"),
     "${DATA_ROOT}/claude"),
    (re.escape(r"${DATA_ROOT}/opencode"),
     "${DATA_ROOT}/opencode"),
    (re.escape(r"${DATA_ROOT}/reasonix"),
     "${DATA_ROOT}/reasonix"),
    (re.escape(r"${DATA_ROOT}/"),
     "${DATA_ROOT}/"),
    (re.escape(r"${WORKSPACE_ROOT}"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"${WORKSPACE_ROOT}/"),
     "${WORKSPACE_ROOT}/"),
    (re.escape(r"${WORKSPACE_ROOT}"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"${DEV_ROOT}"),
     "${DEV_ROOT}"),
    (re.escape(r"${SCRATCH_ROOT}"),
     "${SCRATCH_ROOT}"),
    # User home paths
    (re.escape(r"${USER_HOME}/.config/opencode/skills"),
     "${USER_HOME}/.config/opencode/skills"),
    (re.escape(r"${USER_HOME}/.config/opencode"),
     "${USER_HOME}/.config/opencode"),
    (re.escape(r"${USER_HOME}/.local/share/opencode"),
     "${USER_HOME}/.local/share/opencode"),
    (re.escape(r"${USER_HOME}/.claude"),
     "${USER_HOME}/.claude"),
    (re.escape(r"${USER_HOME}/.codex"),
     "${USER_HOME}/.codex"),
    (re.escape(r"${USER_HOME}/.cursor"),
     "${USER_HOME}/.cursor"),
    (re.escape(r"${USER_HOME}/AppData/Roaming/Cursor"),
     "${USER_HOME}/AppData/Roaming/Cursor"),
    (re.escape(r"${USER_HOME}"),
     "${USER_HOME}"),
]

EXCLUDED_PATHS = {
    # Entire directories
    ".git",
    ".ruff_cache",
    ".pytest_cache",
    "skills",
    "agents",
    ".agents",
    ".codex",
    ".opencode",
    ".obsidian",
    # Tracked curated external skills remain excluded from public export until
    # provenance, licensing, and adaptation review are complete.
    "external-skills",
    # Frame is an architecture template, not a distribution of character
    # skills or product-specific publishers.
    "packages/character-system",
    "shared/packages/character-system",
    "packages/teaching-system",
    # Frame exposes the public packages extension layer as a README-only
    # placeholder; private package implementations stay in their source repo.
    "packages/sci-system",
    "packages/ai-workbench",
    # Local pilot deployment launchers and contract are not framework source.
    "scripts/platform/dsh-pilot.cmd",
    "scripts/platform/dsh.cmd",
    "scripts/platform/Start-DeepSeekHarnessWorkspacePilot.ps1",
    "scripts/platform/deepseek-harness-governance",
    "WORKSPACE_ENGINEERING/evidence",
    "WORKSPACE_ENGINEERING/proposals",
    "scripts/publishing/publish_chatty_ch_system.py",
    "scripts/publishing/character_system_projection.py",
    "scripts/publishing/publish_check_chatty_ch_system.py",
    "scripts/publishing/sync_chatty_ch_system_repo.py",
    "scripts/tests/publishing/test_publish_chatty_ch_system.py",
    "scripts/tests/publishing/test_registered_repo_sync.py",
    # The public skill-collection publisher depends on the private skills
    # source, which Frame intentionally excludes.
    "scripts/publishing/publish_skill_collection.py",
    "scripts/publishing/publish_check_skill_collection.py",
    "scripts/publishing/sync_skill_collection_repo.py",
    "scripts/publishing/sync_skill_collection_repo.py",
    "scripts/tests/publishing/test_publish_skill_collection.py",
    # This test exercises the private generator's machine-path substitution
    # table. The public skeleton receives a scrubbed generator, so retaining
    # the test would make the generated public suite fail by design.
    "scripts/tests/publishing/test_publish_public.py",
    "scripts/tests/publishing/test_publish_policy.py",
    "scripts/tests/publishing/test_publish_rendering.py",
    "scripts/tests/publishing/test_publish_projection.py",
    # This test validates standalone skill sources and CLIs, which Frame omits
    # with the private skills tree.
    "scripts/tests/workspace/test_standalone_skill_contracts.py",
    # These tests exercise private platform hooks, character paths, or local
    # governance registrations that are intentionally absent from Frame.
    "scripts/tests/workspace/test_agent_governance.py",
    "scripts/tests/workspace/test_hermes_workspace_guard.py",
    # These project-private tests rely on governance capabilities and TASK
    # records that the public projection intentionally scrubs.
    "scripts/tests/workspace/test_merge_safety.py",
    "scripts/tests/workspace/test_workflow_check.py",
    "scripts/tests/platform/test_platform_agent_guards.py",
    "scripts/tests/workspace/test_verify_change_scope.py",
    "scripts/tests/workspace/test_workspace_health.py",
    "scripts/tests/workspace/test_startup_context_policy.py",
    "scripts/tests/workspace/test_workspace_cli.py",
    "scripts/tests/workspace/test_plan_change_surface.py",
    "scripts/tests/workspace/test_knowledge_registry.py",
    "scripts/tests/workspace/test_workspace_explain.py",
    "reports",
    "reasonix.toml",
    "README.zh-CN.md",
    "PROJECT_CONTEXT/todo",
    "PROJECT_CONTEXT/references/external_projects.yaml",
    "PROJECT_CONTEXT/reports/history",
    "PROJECT_CONTEXT/tasks/ledger",
    "PROJECT_CONTEXT/tasks/records",
    # These source templates are rendered as root-level public documents.
    "USAGE_GUIDES/QUICK_START/beginner_guide.md",
    "USAGE_GUIDES/QUICK_START/onboarding.md",
    "USAGE_GUIDES/QUICK_START/path_mapping_reference.md",
    "opencode.json",
    "scripts/reporting/report_status.py",
    "scripts/reporting/report_routing_quality.py",
    "scripts/validation/validate_protocols.py",
    "scripts/tests/validation/test_validate_protocols.py",
    "scripts/sync_report.ps1",
    "scripts/tests/reporting/test_report_status.py",
    "mcp/servers",
    "mcp/downloads",
    "mcp/logs",
    "publish-staging",
    "corpus",
    "backups",
    "archives",
    "archive",
    # Subdirectory exclusions (full relative path)
    ".claude/skills",
    "reports/legacy_git_metadata",
    "packages/character-system/distribution",
    "WORKSPACE_ENGINEERING/plans/public-repo-plan.md",
    # Individual files
    ".env",
    ".claude/routing_events.ndjson",
    ".claude/settings.local.json",
}

SCRUB_FILES: set[str] = {
    "workspace_manifest.yaml",
    "AGENTS.md",
    "shared/governance/agent_registry.yaml",
    "shared/governance/agent_governance.yaml",
    "shared/templates/agent_registration.example.yaml",
    "shared/templates/agent_capability_lease.example.yaml",
    "PROJECT_CONTEXT/tasks/registry/index.yaml",
    "PROJECT_CONTEXT/continuity/session_migrations.json",
    "PROJECT_CONTEXT/tasks/ledger/README.md",
    "PROJECT_CONTEXT/continuity/current_status.md",
    "PROJECT_CONTEXT/governance/context_budget.md",
    "USAGE_GUIDES/QUICK_START/claude_code.md",
    "scripts/start_hermes_gateway.ps1",
    "scripts/stop_hermes_gateway.ps1",
    "scripts/claude_long_task_notifications/hermes-mcp-client.js",
    "scripts/workspace/hermes_workspace_guard.py",
    "scripts/workspace/workspace_health.py",
    # Responsibility-package implementations are copied into the framework
    # skeleton. Scrub their machine defaults too; otherwise the public checker
    # sees the implementation's own Windows literals as leaked private paths.
    "scripts/platform/start_hermes_gateway.ps1",
    "scripts/platform/stop_hermes_gateway.ps1",
    "scripts/platform/claude_long_task_notifications/hermes-mcp-client.js",
    "scripts/publishing/publish_check.py",
    "scripts/publishing/publish_public.py",
    "scripts/publishing/publish_policy.py",
    "scripts/publishing/public_workspace_renderer.py",
    "scripts/publishing/sync_chatty_ch_system_repo.py",
    "scripts/publishing/sync_public_repo.py",
    "scripts/workspace/hermes_workspace_guard.py",
    "scripts/workspace/agent_governance.py",
    "scripts/workspace/workspace_health.py",
    "scripts/tests/workspace/test_workspace_cli.py",
    "scripts/tests/workspace/test_hermes_workspace_guard.py",
    "scripts/tests/workspace/test_workspace_health.py",
    "scripts/tests/workspace/test_agent_governance.py",
    ".claude/rules/workspace-boundary.md",
    "reasonix.toml",
    "mcp/README.md",
    "scripts/publishing/sync_public_repo.py",
    "WORKSPACE_ENGINEERING/PUBLISH.md",
}

TEMPLATE_FILES: set[str] = {
    "workspace_manifest.yaml",
    "mcp/configs/installed-local.mcp.json",
    "mcp/configs/wps-agent.mcp.json",
}

SKELETON_DIRS = []

PUBLIC_EXTENSION_LAYERS = ("skills", "external-skills", "packages")

def _compile_substitutions() -> list[tuple[re.Pattern[str], str]]:
    """Compile substitutions for literal and JSON-escaped Windows paths."""
    compiled: list[tuple[re.Pattern[str], str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern_str, repl in SUBSTITUTIONS:
        variants = [pattern_str]
        flexible_slashes = pattern_str.replace(r"\\", r"[\\/]+")
        if flexible_slashes != pattern_str:
            variants.append(flexible_slashes)
        for variant in variants:
            key = (variant, repl)
            if key in seen:
                continue
            compiled.append((re.compile(variant), repl))
            seen.add(key)
    return compiled

def scrub_content(text: str) -> str:
    """Replace all known absolute-path patterns with template variables."""
    for pattern, repl in _compile_substitutions():
        text = pattern.sub(repl, text)
    return text

def should_exclude(rel_path: str) -> bool:
    """Return True if the relative path should be excluded."""
    parts = rel_path.replace("\\", "/").split("/")
    # Check each prefix of the path against EXCLUDED_PATHS
    cumulative = ""
    for part in parts:
        cumulative = (cumulative + "/" + part) if cumulative else part
        if cumulative in EXCLUDED_PATHS:
            return True
    # Check exact file match
    if rel_path.replace("\\", "/") in EXCLUDED_PATHS:
        return True
    # Exclude __pycache__, .pyc, .DS_Store, Thumbs.db
    name = parts[-1] if parts else ""
    if name in ("__pycache__", ".DS_Store", "Thumbs.db"):
        return True
    if name.endswith(".pyc"):
        return True
    if name.endswith(".vbs"):
        return True
    return False

def is_skeleton_dir(rel_path: str) -> str | None:
    """If rel_path falls under a skeleton dir, return the purpose text."""
    norm = rel_path.replace("\\", "/").rstrip("/")
    for sdir, _stub_files, purpose in SKELETON_DIRS:
        if norm == sdir or norm.startswith(sdir + "/"):
            return purpose
    return None

def needs_scrub(rel_path: str) -> bool:
    """Check if a file needs path scrubbing."""
    norm = rel_path.replace("\\", "/")
    # Check exact match
    if norm in SCRUB_FILES:
        return True
    # Check wildcard patterns
    if norm.startswith("reports/"):
        return True
    if "/reports/" in norm:
        return True
    # Task history and outcomes may quote environment-specific paths in
    # evidence; public snapshots keep their structure but scrub their text.
    if norm.startswith("PROJECT_CONTEXT/tasks/ledger/"):
        return True
    if norm.startswith("PROJECT_CONTEXT/tasks/records/"):
        return True
    # Public context keeps generic governance notes but must not carry the
    # source workspace's machine paths.
    if norm.startswith("PROJECT_CONTEXT/"):
        return True
    # All mcp/configs/*.json need scrubbing
    if norm.startswith("mcp/configs/") and norm.endswith(".json"):
        return True
    return False

def is_template(rel_path: str) -> bool:
    """Check if a file should also produce a .template variant."""
    return rel_path.replace("\\", "/") in TEMPLATE_FILES
