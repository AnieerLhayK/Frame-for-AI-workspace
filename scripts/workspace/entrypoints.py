"""Registry of stable root entry points and their implementations."""

from __future__ import annotations

from types import MappingProxyType


ENTRYPOINT_MODULES = MappingProxyType(
    {
        "agent_governance.py": "scripts.workspace.agent_governance",
        "bootstrap_workspace.py": "scripts.workspace.bootstrap_workspace",
        "claude_model_advice.py": "scripts.workspace.claude_model_advice",
        "failure_check.py": "scripts.workspace.failure_check",
        "find_knowledge.py": "scripts.workspace.find_knowledge",
        "hermes_workspace_guard.py": "scripts.workspace.hermes_workspace_guard",
        "merge_safety.py": "scripts.workspace.merge_safety",
        "migration_dry_run.py": "scripts.workspace.migration_dry_run",
        "plan_change_surface.py": "scripts.workspace.plan_change_surface",
        "resolve_task_context.py": "scripts.workspace.resolve_task_context",
        "session_continuity.py": "scripts.workspace.session_continuity",
        "skill_lifecycle.py": "scripts.workspace.skill_lifecycle",
        "task_ledger.py": "scripts.workspace.task_ledger",
        "task_records.py": "scripts.workspace.task_records",
        "verify_change_scope.py": "scripts.workspace.verify_change_scope",
        "workflow_check.py": "scripts.workspace.workflow_check",
        "workspace_cli.py": "scripts.workspace.workspace_cli",
        "workspace_explain.py": "scripts.workspace.workspace_explain",
        "workspace_health.py": "scripts.workspace.workspace_health",
        "workspace_launcher.py": "scripts.workspace.workspace_launcher",
        "workspace_summary.py": "scripts.workspace.workspace_summary",
        "check_doc_pairs.py": "scripts.validation.check_doc_pairs",
        "validate_manifest.py": "scripts.validation.validate_manifest",
        "validate_protocols.py": "scripts.validation.validate_protocols",
        "ci_run.py": "scripts.reporting.ci_run",
        "report_routing_quality.py": "scripts.reporting.report_routing_quality",
        "report_status.py": "scripts.reporting.report_status",
        "publish_chatty_ch_system.py": "scripts.publishing.publish_chatty_ch_system",
        "publish_check.py": "scripts.publishing.publish_check",
        "publish_check_chatty_ch_system.py": "scripts.publishing.publish_check_chatty_ch_system",
        "publish_check_qq_raw_filter.py": "scripts.publishing.publish_check_qq_raw_filter",
        "publish_public.py": "scripts.publishing.publish_public",
        "publish_qq_raw_filter.py": "scripts.publishing.publish_qq_raw_filter",
        "qq_raw_filter_public_checks.py": "scripts.publishing.qq_raw_filter_public_checks",
        "sync_chatty_ch_system_repo.py": "scripts.publishing.sync_chatty_ch_system_repo",
        "sync_public_repo.py": "scripts.publishing.sync_public_repo",
        "sync_qq_raw_filter_repo.py": "scripts.publishing.sync_qq_raw_filter_repo",
    }
)
