from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.workspace_cli import WORKSPACE_ROOT, build_parser, dispatch, powershell_executable


CLI = WORKSPACE_ROOT / "scripts" / "workspace_cli.py"


class WorkspaceCliTests(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        cwd: Path = WORKSPACE_ROOT,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_task_list_delegates_to_registry(self) -> None:
        result = self.run_cli("task", "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("platform_exposure", result.stdout)
        self.assertIn("Registered workspace tasks", result.stdout)

    def test_top_level_help_explains_common_flows(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Common flows:", result.stdout)
        self.assertIn("workspace task resolve <task-id>", result.stdout)
        self.assertIn("workspace explain path scripts/workspace_cli.py", result.stdout)

    def test_task_resolve_preserves_json_output(self) -> None:
        result = self.run_cli(
            "task",
            "resolve",
            "skill_metadata_update",
            "--bind",
            "target-skill=packages/character-system/engineering/generation/character-generator",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task"]["id"], "skill_metadata_update")
        self.assertEqual(payload["status"], "PASS")

    def test_prompt_show_preserves_json_output(self) -> None:
        result = self.run_cli("prompt", "show", "task_routing", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["prompt"]["id"], "task_routing")

    def test_bootstrap_works_from_a_workspace_child(self) -> None:
        result = self.run_cli(
            "bootstrap",
            "--print-json",
            cwd=WORKSPACE_ROOT / "scripts" / "tests",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(Path(payload["workspace_root"]), WORKSPACE_ROOT)

    def test_health_delegates_optional_tests(self) -> None:
        args = build_parser().parse_args(["health", "--with-tests", "--format", "json"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "workspace_health.py")
        self.assertIn("--with-tests", command)

    def test_summary_delegates_recent_limit_and_format(self) -> None:
        args = build_parser().parse_args(["summary", "--recent", "3", "--format", "json"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "workspace_summary.py")
        self.assertIn("3", command)
        self.assertIn("json", command)

    def test_sessions_audit_delegates_migration_id(self) -> None:
        args = build_parser().parse_args(
            ["sessions", "audit", "--migration-id", "character-package-20260614"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "session_continuity.py")
        self.assertIn("character-package-20260614", command)

    def test_agent_check_delegates_identity_path_and_lease(self) -> None:
        args = build_parser().parse_args(
            [
                "agent",
                "check",
                "--agent",
                "hermes",
                "--path",
                "workspace_manifest.yaml",
                "--skill",
                "style-doctor",
                "--lease",
                "D:/leases/demo.yaml",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "agent_governance.py")
        self.assertIn("hermes", command)
        self.assertIn("workspace_manifest.yaml", command)
        self.assertIn("style-doctor", command)
        self.assertIn("D:/leases/demo.yaml", command)

    def test_agent_list_delegates_to_registration_tool(self) -> None:
        args = build_parser().parse_args(["agent", "list", "--format", "json"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "agent_governance.py")
        self.assertIn("list", command)

    def test_agent_show_validate_and_doctor_delegate_agent_id(self) -> None:
        for action in ("show", "validate", "doctor"):
            with self.subTest(action=action):
                args = build_parser().parse_args(["agent", action, "cursor"])
                with patch("scripts.workspace_cli.run_command", return_value=0) as run:
                    self.assertEqual(dispatch(args), 0)
                command = run.call_args.args[0]
                self.assertIn(action, command)
                self.assertIn("cursor", command)

    def test_agent_request_delegates_multiple_paths(self) -> None:
        args = build_parser().parse_args(
            [
                "agent",
                "request",
                "--agent",
                "opencode",
                "--mode",
                "worktree",
                "--summary",
                "Propose registry change",
                "--path",
                "workspace_manifest.yaml",
                "--path",
                "shared/workspace_policy.md",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(command.count("--path"), 2)
        self.assertIn("worktree", command)

    def test_agent_lease_validate_delegates_file(self) -> None:
        args = build_parser().parse_args(
            ["agent", "lease", "validate", "D:/leases/demo.yaml", "--format", "json"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertIn("validate", command)
        self.assertIn("D:/leases/demo.yaml", command)

    def test_skill_init_delegates_scaffold_options(self) -> None:
        args = build_parser().parse_args(
            [
                "skill",
                "init",
                "demo",
                "--source-path",
                "skills/demo",
                "--description",
                "Demo skill.",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "skill_lifecycle.py")
        self.assertIn("skills/demo", command)
        self.assertIn("Demo skill.", command)

    def test_skill_validate_delegates_target(self) -> None:
        args = build_parser().parse_args(["skill", "validate", "character-generator"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        self.assertIn("character-generator", run.call_args.args[0])

    def test_skill_list_delegates_platform_filter(self) -> None:
        args = build_parser().parse_args(["skill", "list", "--platform", "codex"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        self.assertIn("codex", run.call_args.args[0])

    def test_skill_expose_requires_apply_flag_to_be_forwarded(self) -> None:
        args = build_parser().parse_args(
            ["skill", "expose", "zyc", "--platform", "codex", "--apply"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertIn("zyc", command)
        self.assertIn("--apply", command)

    def test_launcher_install_delegates_dry_run_and_target(self) -> None:
        args = build_parser().parse_args(
            ["launcher", "install", "--install-dir", "D:/tools/bin", "--dry-run"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "workspace_launcher.py")
        self.assertIn("D:/tools/bin", command)
        self.assertIn("--dry-run", command)

    def test_failure_check_delegates_bindings_and_optional_mode(self) -> None:
        args = build_parser().parse_args(
            [
                "failure",
                "check",
                "skill_metadata_update",
                "--bind",
                "target-skill=packages/character-system/engineering/generation/character-generator",
                "--include-optional",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "failure_check.py")
        self.assertIn("target-skill=packages/character-system/engineering/generation/character-generator", command)
        self.assertIn("--include-optional", command)

    def test_preflight_forces_strict_budget(self) -> None:
        args = build_parser().parse_args(["preflight", "platform_exposure"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        self.assertIn("--strict-budget", run.call_args.args[0])

    def test_validate_manifest_delegates_to_existing_validator(self) -> None:
        args = build_parser().parse_args(["validate", "manifest"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        self.assertEqual(
            Path(run.call_args.args[0][1]).name,
            "validate_manifest.py",
        )

    def test_report_status_delegates_to_read_only_checker(self) -> None:
        args = build_parser().parse_args(
            ["reports", "status", "--report-id", "workspace", "--strict"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "report_status.py")
        self.assertIn("--strict", command)

    def test_report_refresh_delegates_to_named_generator(self) -> None:
        args = build_parser().parse_args(["reports", "refresh", "protocol-validation"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        self.assertEqual(Path(run.call_args.args[0][1]).name, "validate_protocols.py")

    def test_change_plan_delegates_options_without_interpreting_them(self) -> None:
        args = build_parser().parse_args(
            [
                "changes",
                "plan",
                "developer_interface_tooling",
                "--intent",
                "tooling",
                "--option",
                "implementation=scripts/workspace_cli.py",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "plan_change_surface.py")
        self.assertIn("implementation=scripts/workspace_cli.py", command)

    def test_change_verify_delegates_task_bindings_and_flags(self) -> None:
        args = build_parser().parse_args(
            [
                "changes",
                "verify",
                "skill_metadata_update",
                "--bind",
                "target-skill=skills/demo",
                "--strict",
                "--no-include-untracked",
                "--agent",
                "hermes",
                "--skill",
                "style-doctor",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "verify_change_scope.py")
        self.assertIn("skill_metadata_update", command)
        self.assertIn("target-skill=skills/demo", command)
        self.assertIn("--strict", command)
        self.assertIn("--no-include-untracked", command)
        self.assertIn("hermes", command)
        self.assertIn("style-doctor", command)

    def test_workflow_check_delegates_without_running_git_writes(self) -> None:
        args = build_parser().parse_args(
            [
                "workflow",
                "check",
                "skill_metadata_update",
                "--bind",
                "target-skill=skills/demo",
                "--strict",
                "--agent",
                "hermes",
                "--skill",
                "style-doctor",
            ]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "workflow_check.py")
        self.assertIn("skill_metadata_update", command)
        self.assertIn("target-skill=skills/demo", command)
        self.assertIn("--strict", command)
        self.assertIn("hermes", command)
        self.assertIn("style-doctor", command)

    def test_knowledge_find_delegates_query_and_layer(self) -> None:
        args = build_parser().parse_args(
            ["knowledge", "find", "skill 开发", "--layer", "workspace_engineering"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "find_knowledge.py")
        self.assertIn("skill 开发", command)
        self.assertIn("workspace_engineering", command)

    def test_knowledge_validate_delegates_without_a_query(self) -> None:
        args = build_parser().parse_args(["knowledge", "validate", "--format", "json"])
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertIn("--validate", command)
        self.assertNotIn("--query", command)

    def test_validate_links_prints_long_paths_on_separate_lines(self) -> None:
        if not (shutil.which("powershell.exe") or shutil.which("pwsh")):
            self.skipTest("PowerShell is required for workspace validate links integration output.")
        result = self.run_cli("validate", "links")
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertIn("\n  LinkPath: ", result.stdout)
        self.assertIn("\n  ExpectedTarget: ", result.stdout)
        self.assertNotIn("ExpectedT\r\n", result.stdout)
        self.assertNotIn("${WORKSPACE_ROOT}\\...", result.stdout)

    def test_link_scripts_avoid_truncating_format_table_output(self) -> None:
        for relative_path in ("scripts/check_links.ps1", "scripts/setup_links.ps1"):
            text = (WORKSPACE_ROOT / relative_path).read_text(encoding="utf-8-sig")
            self.assertNotIn("Format-Table", text)

    def test_powershell_executable_prefers_available_pwsh_fallback(self) -> None:
        with patch("scripts.workspace_cli.shutil.which") as which:
            which.side_effect = lambda name: "pwsh" if name == "pwsh" else None
            self.assertEqual(powershell_executable(), "pwsh")

    def test_validate_links_uses_resolved_powershell_executable(self) -> None:
        args = build_parser().parse_args(["validate", "links"])
        with (
            patch("scripts.workspace_cli.powershell_executable", return_value="pwsh"),
            patch("scripts.workspace_cli.run_command", return_value=0) as run,
        ):
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "pwsh")

    def test_explain_path_delegates_to_explain_tool(self) -> None:
        args = build_parser().parse_args(
            ["explain", "--format", "json", "path", "scripts/workspace_cli.py"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "workspace_explain.py")
        self.assertIn("path", command)
        self.assertIn("scripts/workspace_cli.py", command)
        self.assertEqual(command[command.index("--format") + 1], "json")

    def test_explain_accepts_subcommand_format_option(self) -> None:
        args = build_parser().parse_args(
            ["explain", "path", "scripts/workspace_cli.py", "--format", "json"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--format") + 1], "json")

    def test_explain_topic_delegates_limit(self) -> None:
        args = build_parser().parse_args(
            ["explain", "topic", "developer interface", "--limit", "2"]
        )
        with patch("scripts.workspace_cli.run_command", return_value=0) as run:
            self.assertEqual(dispatch(args), 0)
        command = run.call_args.args[0]
        self.assertIn("topic", command)
        self.assertIn("developer interface", command)
        self.assertIn("2", command)


if __name__ == "__main__":
    unittest.main()
