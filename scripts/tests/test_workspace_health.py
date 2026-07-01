from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path, PurePosixPath
from unittest.mock import patch

import yaml

from scripts.workspace_health import (
    CheckResult,
    HERMES_GUARD_SCRIPT,
    WORKSPACE_ROOT,
    check_claude_model_routing,
    check_hermes_guard,
    check_hygiene,
    check_platform_agent_guards,
    render_text,
    run_health,
)


def completed(command: list[str], returncode: int, payload: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        command,
        returncode,
        stdout=json.dumps(payload) if payload is not None else "",
        stderr="",
    )


def check_hermes_guard_fixture(status: str) -> CheckResult:
    return CheckResult(
        "hermes-guard",
        status,
        "Hermes runtime governance fixture.",
    )


def check_platform_guard_fixture(status: str) -> CheckResult:
    return CheckResult(
        "platform-agent-guards",
        status,
        "Platform governance fixture.",
    )


class WorkspaceHealthTests(unittest.TestCase):
    def healthy_runner(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        executable = Path(command[1]).name if len(command) > 1 else command[0]
        if executable == "bootstrap_workspace.py":
            return completed(command, 0, {"source_of_truth": str(WORKSPACE_ROOT)})
        if executable == "find_knowledge.py":
            return completed(command, 0, {"status": "PASS", "topic_count": 12, "entry_count": 31})
        if executable == "report_status.py":
            return completed(
                command,
                0,
                {"reports": [{"report_id": "workspace", "status": "FRESH"}]},
            )
        return completed(command, 0)

    def test_default_health_passes_without_tests(self) -> None:
        payload = run_health(
            runner=self.healthy_runner,
            hermes_guard_checker=lambda: check_hermes_guard_fixture("PASS"),
            platform_guard_checker=lambda: check_platform_guard_fixture("PASS"),
        )
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["with_tests"])
        self.assertNotIn("tests", [check["check_id"] for check in payload["checks"]])

    def test_with_tests_adds_test_check(self) -> None:
        payload = run_health(
            with_tests=True,
            runner=self.healthy_runner,
            hermes_guard_checker=lambda: check_hermes_guard_fixture("PASS"),
            platform_guard_checker=lambda: check_platform_guard_fixture("PASS"),
        )
        self.assertEqual(payload["status"], "PASS")
        self.assertIn("tests", [check["check_id"] for check in payload["checks"]])

    def test_text_render_groups_checks_and_explains_skipped_tests(self) -> None:
        payload = run_health(
            runner=self.healthy_runner,
            hermes_guard_checker=lambda: check_hermes_guard_fixture("PASS"),
            platform_guard_checker=lambda: check_platform_guard_fixture("PASS"),
        )
        output = StringIO()
        with redirect_stdout(output):
            render_text(payload)
        text = output.getvalue()
        self.assertIn("Core Workspace", text)
        self.assertIn("Claude Code Boundary", text)
        self.assertIn("Agent Runtime Guards", text)
        self.assertIn("Script test suite: SKIPPED", text)
        self.assertIn("workspace health --with-tests", text)

    def test_hygiene_fails_when_root_cache_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".pytest_cache").mkdir()
            result = check_hygiene(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn(".pytest_cache", result.summary)

    def test_hygiene_passes_without_root_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in (
                "CLAUDE.md",
                ".claude/project-boundary.json",
                ".claude/rules/workspace-boundary.md",
                ".claude/settings.json",
                ".claude/model-routing-advice.json",
                ".claude/hooks/model_routing_guard.ps1",
                ".claude/hooks/workspace_boundary_guard.ps1",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test", encoding="utf-8")
            result = check_hygiene(root)
        self.assertEqual(result.status, "PASS")

    def test_hygiene_fails_when_external_project_appears(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "claude").mkdir()
            result = check_hygiene(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("claude", result.summary)

    def write_model_routing_fixture(self, root: Path, *, include_policy: bool = True) -> None:
        (root / "shared" / "claude" / "policies").mkdir(parents=True, exist_ok=True)
        claude_lines = [
            "# Workspace Agent Instructions",
            "@AGENTS.md",
        ]
        if include_policy:
            claude_lines.append("@shared/claude/policies/model-routing-policy.md")
        claude_lines.extend(
            [
                "",
                "Treat model-routing guidance as a visible recommendation only; it must never",
                "edit model configuration, provider settings, plugins, or permission policy.",
                "Apply model-routing guidance only when .claude/model-routing-advice.json is enabled.",
            ]
        )
        (root / "CLAUDE.md").write_text("\n".join(claude_lines), encoding="utf-8")
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "model-routing-advice.json").write_text(
            json.dumps({"interface_version": 1, "enabled": True}, ensure_ascii=False),
            encoding="utf-8",
        )
        (root / "shared" / "claude" / "policies" / "model-routing-policy.md").write_text(
            "\n".join(
                [
                    "# Model Routing Policy",
                    "## 执行时机（强制）",
                    "## Manual Toggle",
                    ".claude/model-routing-advice.json",
                    '"enabled": false',
                    "This controls advice injection and pre-tool enforcement.",
                    "## First Response Format",
                    "This applies repeatedly inside the same Claude Code session.",
                    "Do not suppress the assessment merely because an earlier turn already recommended Pro.",
                    "The assessment must appear before any tool call.",
                    "The parent Claude response must show it before subagent/Agent delegation.",
                    "Do not downgrade a task to Flash merely because the user asks for read-only planning.",
                    "Read-only workspace guard or permission design still warrants Pro.",
                    "Claude Code, Codex, OpenCode, and Hermes guard design is Pro-class.",
                    "workspace health failures with workflow out-of-scope errors are Pro-class.",
                    "Git merge conflicts are Pro-class.",
                    "prompt_registry.yaml conflicts are Pro-class.",
                    "pause after the visible recommendation before substantive work.",
                    "The user may explicitly continue with the current model.",
                    "任务复杂度评估：Flash sufficient。原因：<简短原因>。",
                    "> 任务复杂度评估：Recommend Pro",
                    "> 原因：<具体原因>",
                    "> 模型建议：建议切换到 `deepseek-v4-pro`；我继续使用当前模型工作，由你决定是否切换。",
                    "> 权限边界：模型建议不改变 write scope、Git 检查或 workspace governance。",
                    "## Authority Boundary",
                    "It must never be satisfied by editing LiteLLM configuration.",
                    "Model strength is not authority.",
                    "No workspace governance rule is weakened.",
                ]
            ),
            encoding="utf-8",
        )

    def test_claude_model_routing_policy_passes_when_loaded_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_routing_fixture(root)
            result = check_claude_model_routing(root)
        self.assertEqual(result.status, "PASS")

    def test_claude_model_routing_policy_passes_when_toggle_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_routing_fixture(root)
            (root / ".claude" / "model-routing-advice.json").write_text(
                json.dumps({"interface_version": 1, "enabled": False}, ensure_ascii=False),
                encoding="utf-8",
            )
            result = check_claude_model_routing(root)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.details["toggle_enabled"], False)
        self.assertIn("disabled by toggle", result.summary)

    def test_claude_model_routing_policy_fails_without_claude_include(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_routing_fixture(root, include_policy=False)
            result = check_claude_model_routing(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("CLAUDE.md", " ".join(result.details["findings"]))

    def test_claude_model_routing_policy_fails_without_first_response_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_routing_fixture(root)
            policy = root / "shared" / "claude" / "policies" / "model-routing-policy.md"
            policy.write_text(
                "\n".join(
                    [
                        "# Model Routing Policy",
                        "## 执行时机（强制）",
                        "## Authority Boundary",
                        "It must never be satisfied by editing LiteLLM configuration.",
                        "Model strength is not authority.",
                        "No workspace governance rule is weakened.",
                    ]
                ),
                encoding="utf-8",
            )
            result = check_claude_model_routing(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("first response format", " ".join(result.details["findings"]))

    def test_claude_model_routing_policy_fails_without_authority_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_routing_fixture(root)
            policy = root / "shared" / "claude" / "policies" / "model-routing-policy.md"
            policy.write_text(
                "\n".join(
                    [
                        "# Model Routing Policy",
                        "## 执行时机（强制）",
                        "## First Response Format",
                        "This applies repeatedly inside the same Claude Code session.",
                        "Do not suppress the assessment merely because an earlier turn already recommended Pro.",
                        "The assessment must appear before any tool call.",
                        "The parent Claude response must show it before subagent/Agent delegation.",
                        "Do not downgrade a task to Flash merely because the user asks for read-only planning.",
                        "Read-only workspace guard or permission design still warrants Pro.",
                        "Claude Code, Codex, OpenCode, and Hermes guard design is Pro-class.",
                        "workspace health failures with workflow out-of-scope errors are Pro-class.",
                        "Git merge conflicts are Pro-class.",
                        "prompt_registry.yaml conflicts are Pro-class.",
                        "任务复杂度评估：Flash sufficient。原因：<简短原因>。",
                        "> 任务复杂度评估：Recommend Pro",
                        "> 权限边界：模型建议不改变 write scope、Git 检查或 workspace governance。",
                    ]
                ),
                encoding="utf-8",
            )
            result = check_claude_model_routing(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("authority boundary", " ".join(result.details["findings"]))

    def test_stale_report_needs_attention(self) -> None:
        def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
            if len(command) > 1 and Path(command[1]).name == "report_status.py":
                return completed(
                    command,
                    2,
                    {"reports": [{"report_id": "workspace", "status": "STALE"}]},
                )
            return self.healthy_runner(command)

        payload = run_health(
            runner=runner,
            hermes_guard_checker=lambda: check_hermes_guard_fixture("PASS"),
            platform_guard_checker=lambda: check_platform_guard_fixture("PASS"),
        )
        self.assertEqual(payload["status"], "NEEDS_ATTENTION")

    def test_invalid_json_is_an_execution_error(self) -> None:
        def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
            if len(command) > 1 and Path(command[1]).name == "find_knowledge.py":
                return subprocess.CompletedProcess(command, 0, stdout="not-json", stderr="")
            return self.healthy_runner(command)

        payload = run_health(
            runner=runner,
            hermes_guard_checker=lambda: check_hermes_guard_fixture("PASS"),
            platform_guard_checker=lambda: check_platform_guard_fixture("PASS"),
        )
        self.assertEqual(payload["status"], "ERROR")

    def test_hermes_guard_passes_for_bounded_runtime_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = (
                "${DATA_ROOT}/hermes/hermes-agent/venv/Scripts/python.exe "
                "${WORKSPACE_ROOT}/scripts/hermes_workspace_guard.py"
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "terminal:",
                        "  cwd: ${DATA_ROOT}/hermes/cache/staging",
                        "skills:",
                        "  guard_agent_created: true",
                        "hooks:",
                        "  pre_tool_call:",
                        f"    - command: {command}",
                        "      matcher: patch|write_file|terminal|skill_manage|execute_code|process|mcp_.*",
                        "  post_tool_call:",
                        f"    - command: {command}",
                        "  pre_llm_call:",
                        f"    - command: {command}",
                        "mcp_servers:",
                        "  filesystem:",
                        "    args:",
                        "      - ${DATA_ROOT}/hermes",
                        "      - ${DATA_ROOT}/out",
                        "      - ${WORKSPACE_ROOT}/packages/character-system/shared",
                        "      - ${WORKSPACE_ROOT}/packages/character-system/reports/runtime-loop",
                        "    tools:",
                        "      exclude:",
                        "        - write_file",
                        "        - edit_file",
                        "        - create_directory",
                        "        - move_file",
                    ]
                ),
                encoding="utf-8",
            )
            allowlist = root / "allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "approvals": [
                            {
                                "event": event,
                                "command": command,
                                "script_mtime_at_approval": (
                                    datetime.fromtimestamp(
                                        HERMES_GUARD_SCRIPT.stat().st_mtime,
                                        tz=timezone.utc,
                                    )
                                    .isoformat()
                                    .replace("+00:00", "Z")
                                ),
                            }
                            for event in (
                                "pre_tool_call",
                                "post_tool_call",
                                "pre_llm_call",
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = check_hermes_guard(config, allowlist)
        self.assertEqual(result.status, "PASS")

    def test_hermes_guard_rejects_changed_script_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = (
                "${DATA_ROOT}/hermes/hermes-agent/venv/Scripts/python.exe "
                "${WORKSPACE_ROOT}/scripts/hermes_workspace_guard.py"
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "terminal:",
                        "  cwd: ${DATA_ROOT}/hermes/cache/staging",
                        "skills:",
                        "  guard_agent_created: true",
                        "hooks:",
                        "  pre_tool_call:",
                        f"    - command: {command}",
                        "      matcher: patch|write_file|terminal|skill_manage|execute_code|process|mcp_.*",
                        "  post_tool_call:",
                        f"    - command: {command}",
                        "  pre_llm_call:",
                        f"    - command: {command}",
                        "mcp_servers:",
                        "  filesystem:",
                        "    args:",
                        "      - ${DATA_ROOT}/hermes",
                        "      - ${DATA_ROOT}/out",
                        "      - ${WORKSPACE_ROOT}/packages/character-system/shared",
                        "      - ${WORKSPACE_ROOT}/packages/character-system/reports/runtime-loop",
                        "    tools:",
                        "      exclude: [write_file, edit_file, create_directory, move_file]",
                    ]
                ),
                encoding="utf-8",
            )
            allowlist = root / "allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "approvals": [
                            {
                                "event": event,
                                "command": command,
                                "script_mtime_at_approval": "2000-01-01T00:00:00Z",
                            }
                            for event in (
                                "pre_tool_call",
                                "post_tool_call",
                                "pre_llm_call",
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = check_hermes_guard(config, allowlist)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("changed after approval", " ".join(result.details["findings"]))

    def test_hermes_guard_rejects_missing_runtime_loop_read_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = (
                "${DATA_ROOT}/hermes/hermes-agent/venv/Scripts/python.exe "
                "${WORKSPACE_ROOT}/scripts/hermes_workspace_guard.py"
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "terminal:",
                        "  cwd: ${DATA_ROOT}/hermes/cache/staging",
                        "skills:",
                        "  guard_agent_created: true",
                        "hooks:",
                        "  pre_tool_call:",
                        f"    - command: {command}",
                        "      matcher: patch|write_file|terminal|skill_manage|execute_code|process|mcp_.*",
                        "  post_tool_call:",
                        f"    - command: {command}",
                        "  pre_llm_call:",
                        f"    - command: {command}",
                        "mcp_servers:",
                        "  filesystem:",
                        "    args: [${DATA_ROOT}/hermes, ${DATA_ROOT}/out]",
                        "    tools:",
                        "      exclude: [write_file, edit_file, create_directory, move_file]",
                    ]
                ),
                encoding="utf-8",
            )
            mtime = (
                datetime.fromtimestamp(
                    HERMES_GUARD_SCRIPT.stat().st_mtime,
                    tz=timezone.utc,
                )
                .isoformat()
                .replace("+00:00", "Z")
            )
            allowlist = root / "allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "approvals": [
                            {
                                "event": event,
                                "command": command,
                                "script_mtime_at_approval": mtime,
                            }
                            for event in (
                                "pre_tool_call",
                                "post_tool_call",
                                "pre_llm_call",
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = check_hermes_guard(config, allowlist)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("runtime-loop read roots", " ".join(result.details["findings"]))

    def test_hermes_guard_rejects_broad_filesystem_and_missing_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "terminal:",
                        "  cwd: ${WORKSPACE_ROOT}",
                        "skills:",
                        "  guard_agent_created: false",
                        "hooks: {}",
                        "mcp_servers:",
                        "  filesystem:",
                        "    args: [${WORKSPACE_ROOT}, ${DEV_ROOT}]",
                    ]
                ),
                encoding="utf-8",
            )
            allowlist = root / "allowlist.json"
            allowlist.write_text('{"approvals": []}', encoding="utf-8")
            result = check_hermes_guard(config, allowlist)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("broad drive root", " ".join(result.details["findings"]))

    def test_platform_agent_guards_pass_for_tracked_configuration(self) -> None:
        with patch(
            "scripts.workspace_health.WORKSPACE_ROOT",
            PurePosixPath("/home/runner/work/workspace/workspace"),
        ):
            result = check_platform_agent_guards()
        self.assertEqual(result.status, "PASS", result.details)

    def test_platform_agent_guards_reject_cursor_write_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "agent_registry.yaml"
            payload = yaml.safe_load(
                (WORKSPACE_ROOT / "shared" / "agent_registry.yaml").read_text(
                    encoding="utf-8-sig"
                )
            )
            payload["agents"]["cursor"]["capabilities"]["allow"] = ["source_write"]
            registry.write_text(
                yaml.safe_dump(payload, sort_keys=False),
                encoding="utf-8",
            )
            result = check_platform_agent_guards(registry_path=registry)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("Cursor", " ".join(result.details["findings"]))


@unittest.skipUnless(
    os.name == "nt" and shutil.which("powershell.exe"),
    "Claude boundary hook tests require Windows PowerShell.",
)
class ClaudeBoundaryGuardTests(unittest.TestCase):
    guard_path = WORKSPACE_ROOT / ".claude" / "hooks" / "workspace_boundary_guard.ps1"

    def run_guard(self, payload: dict, project_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
        return self.run_guard_text(
            json.dumps(payload, ensure_ascii=False),
            project_dir=project_dir,
        )

    def run_guard_text(self, payload_text: str, project_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(project_dir or WORKSPACE_ROOT)
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.guard_path),
            ],
            input=payload_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=False,
        )

    def test_native_edit_inside_workspace_is_allowed(self) -> None:
        result = self.run_guard(
            {
                "cwd": str(WORKSPACE_ROOT),
                "tool_name": "Edit",
                "tool_input": {"file_path": str(WORKSPACE_ROOT / "README.md")},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_edit_in_external_project_requires_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "README.md"
            result = self.run_guard(
                {
                    "cwd": str(WORKSPACE_ROOT),
                    "tool_name": "Edit",
                    "tool_input": {"file_path": str(target)},
                }
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Start a new Claude session", result.stderr)
        self.assertIn("Do not bypass this guard", result.stderr)

    def test_wrapped_powershell_external_write_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "README.md"
            result = self.run_guard(
                {
                    "cwd": str(WORKSPACE_ROOT),
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": (
                            'powershell -Command "Set-Content -LiteralPath '
                            f'{target} -Value test"'
                        )
                    },
                }
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("wrapped shell command", result.stderr)


@unittest.skipUnless(
    os.name == "nt" and shutil.which("powershell.exe"),
    "Claude model-routing hook tests require Windows PowerShell.",
)
class ClaudeModelRoutingGuardTests(unittest.TestCase):
    guard_path = WORKSPACE_ROOT / ".claude" / "hooks" / "model_routing_guard.ps1"

    def run_guard(self, payload: dict, project_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
        return self.run_guard_text(
            json.dumps(payload, ensure_ascii=False),
            project_dir=project_dir,
        )

    def run_guard_text(self, payload_text: str, project_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(project_dir or WORKSPACE_ROOT)
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.guard_path),
            ],
            input=payload_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=False,
        )

    def write_transcript(self, path: Path, entries: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries),
            encoding="utf-8",
        )

    def write_model_advice_toggle(self, root: Path, *, enabled: bool) -> None:
        toggle = root / ".claude" / "model-routing-advice.json"
        toggle.parent.mkdir(parents=True, exist_ok=True)
        toggle.write_text(
            json.dumps({"interface_version": 1, "enabled": enabled}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_user_prompt_submit_injects_visible_assessment_context(self) -> None:
        result = self.run_guard({"hook_event_name": "UserPromptSubmit"})
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        additional = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Flash sufficient", additional)
        self.assertIn("Recommend Pro", additional)
        self.assertIn("before any tool call", additional)
        self.assertIn("pause for the user", additional)

    def test_user_prompt_submit_falls_back_when_prompt_json_is_corrupt(self) -> None:
        payload_text = (
            '{"hook_event_name":"UserPromptSubmit",'
            '"transcript_path":"${WORKSPACE_ROOT}\\\\session.jsonl",'
            '"prompt":"unterminated text}'
        )
        result = self.run_guard_text(payload_text)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        additional = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Flash sufficient", additional)

    def test_pre_tool_use_blocks_before_visible_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.jsonl"
            self.write_transcript(
                transcript,
                [
                    {"message": {"role": "user", "content": "high risk task"}},
                    {
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "tool_use", "name": "Read"}],
                        }
                    },
                ],
            )
            result = self.run_guard(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "transcript_path": str(transcript),
                }
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("model-tier assessment", result.stderr)

    def test_pre_tool_use_blocks_after_pro_assessment_without_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.jsonl"
            self.write_transcript(
                transcript,
                [
                    {"message": {"role": "user", "content": "high risk task"}},
                    {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "> 任务复杂度评估：Recommend Pro",
                                }
                            ],
                        }
                    },
                ],
            )
            result = self.run_guard(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "transcript_path": str(transcript),
                }
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Recommend Pro was issued", result.stderr)

    def test_pre_tool_use_allows_after_flash_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.jsonl"
            self.write_transcript(
                transcript,
                [
                    {"message": {"role": "user", "content": "summarize a short log"}},
                    {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "任务复杂度评估：Flash sufficient。原因：低风险。",
                                }
                            ],
                        }
                    },
                ],
            )
            result = self.run_guard(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "transcript_path": str(transcript),
                }
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pre_tool_use_allows_after_user_confirms_current_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.jsonl"
            self.write_transcript(
                transcript,
                [
                    {"message": {"role": "user", "content": "high risk task"}},
                    {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "> 任务复杂度评估：Recommend Pro",
                                }
                            ],
                        }
                    },
                    {"message": {"role": "user", "content": "继续使用当前模型"}},
                ],
            )
            result = self.run_guard(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "transcript_path": str(transcript),
                }
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_user_prompt_submit_is_silent_when_model_advice_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_advice_toggle(root, enabled=False)
            result = self.run_guard({"hook_event_name": "UserPromptSubmit"}, project_dir=root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_pre_tool_use_allows_without_assessment_when_model_advice_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_model_advice_toggle(root, enabled=False)
            transcript = root / "transcript.jsonl"
            self.write_transcript(
                transcript,
                [
                    {"message": {"role": "user", "content": "high risk task"}},
                    {
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "tool_use", "name": "Read"}],
                        }
                    },
                ],
            )
            result = self.run_guard(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "transcript_path": str(transcript),
                },
                project_dir=root,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
