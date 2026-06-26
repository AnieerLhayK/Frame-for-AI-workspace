from __future__ import annotations

import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from scripts import hermes_workspace_guard as guard


class HermesWorkspaceGuardTests(unittest.TestCase):
    def payload(
        self,
        tool: str,
        tool_input: dict,
        *,
        event: str = "pre_tool_call",
        cwd: str = r"${WORKSPACE_ROOT}",
    ) -> dict:
        return {
            "hook_event_name": event,
            "tool_name": tool,
            "tool_input": tool_input,
            "session_id": "session-demo",
            "cwd": cwd,
        }

    def test_blocks_native_patch_to_workspace_skill_source(self) -> None:
        result = guard.evaluate(
            self.payload(
                "patch",
                {
                    "path": (
                        r"${WORKSPACE_ROOT}\packages\character-system\runtime"
                        r"\characters\zyc\references\voice_card.md"
                    )
                },
            )
        )
        self.assertEqual(result["action"], "block")
        self.assertIn("record_producer", result["message"])

    def test_allows_diagnosis_record_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                guard.evaluate(
                    self.payload(
                        "skill_view",
                        {"name": "style-doctor"},
                        event="post_tool_call",
                    )
                )
                result = guard.evaluate(
                    self.payload(
                        "write_file",
                        {
                            "path": (
                                r"${WORKSPACE_ROOT}\packages\character-system"
                                r"\reports\runtime-loop\diagnoses\DIAG-demo.md"
                            )
                        },
                    )
                )
        self.assertEqual(result, {})

    def test_blocks_character_record_without_active_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                result = guard.evaluate(
                    self.payload(
                        "write_file",
                        {
                            "path": (
                                r"${WORKSPACE_ROOT}\packages\character-system"
                                r"\reports\runtime-loop\diagnoses\DIAG-demo.md"
                            )
                        },
                    )
                )
        self.assertEqual(result["action"], "block")
        self.assertIn("active record-writing Skill", result["message"])

    def test_blocks_projection_write_through_path(self) -> None:
        result = guard.evaluate(
            self.payload(
                "patch",
                {
                    "path": (
                        r"${DATA_ROOT}/hermes\skills\zyc\references"
                        r"\voice_card.md"
                    )
                },
            )
        )
        self.assertEqual(result["action"], "block")

    def test_blocks_unclassified_terminal_in_workspace(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {"command": "Set-Content README.md changed"},
            )
        )
        self.assertEqual(result["action"], "block")

    def test_allows_read_only_terminal_in_workspace(self) -> None:
        result = guard.evaluate(
            self.payload("terminal", {"command": "git status --short"})
        )
        self.assertEqual(result, {})

    def test_blocks_read_only_prefix_followed_by_mutation(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {
                    "command": (
                        "git status --short; "
                        "Set-Content packages/character-system/runtime/"
                        "characters/zyc/SKILL.md changed"
                    )
                },
            )
        )
        self.assertEqual(result["action"], "block")

    def test_blocks_read_only_command_with_redirection(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {"command": "git status --short > status.txt"},
            )
        )
        self.assertEqual(result["action"], "block")

    def test_allows_agent_request_command(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {
                    "command": (
                        "python scripts/workspace_cli.py agent request "
                        "--agent hermes --summary test --path README.md"
                    )
                },
            )
        )
        self.assertEqual(result, {})

    def test_blocks_agent_request_followed_by_mutation(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {
                    "command": (
                        "python scripts/workspace_cli.py agent request "
                        "--agent hermes --summary test --path README.md; "
                        "Set-Content README.md changed"
                    )
                },
            )
        )
        self.assertEqual(result["action"], "block")

    def test_honors_terminal_tool_cwd_override(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {
                    "command": "Set-Content README.md changed",
                    "cwd": r"${WORKSPACE_ROOT}",
                },
                cwd=r"${DATA_ROOT}/hermes\cache\staging",
            )
        )
        self.assertEqual(result["action"], "block")

    def test_allows_unclassified_terminal_outside_workspace(self) -> None:
        result = guard.evaluate(
            self.payload(
                "terminal",
                {"command": "python do_work.py"},
                cwd=r"D:\external-project",
            )
        )
        self.assertEqual(result, {})

    def test_workspace_skill_keeps_terminal_guard_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                guard.evaluate(
                    self.payload(
                        "skill_view",
                        {"name": "zyc"},
                        event="post_tool_call",
                    )
                )
                result = guard.evaluate(
                    self.payload(
                        "terminal",
                        {"command": "python do_work.py"},
                        cwd=r"D:\external-project",
                    )
                )
        self.assertEqual(result["action"], "block")

    def test_explicit_workspace_path_keeps_terminal_guard_outside_workspace(self) -> None:
        with patch.object(
            guard,
            "WORKSPACE_ROOT",
            PurePosixPath("/home/runner/work/workspace/workspace"),
        ):
            result = guard.evaluate(
                self.payload(
                    "terminal",
                    {
                        "command": (
                            "Set-Content "
                            r"${WORKSPACE_ROOT}\README.md changed"
                        )
                    },
                    cwd=r"D:\external-project",
                )
            )
        self.assertEqual(result["action"], "block")

    def test_blocks_execute_code(self) -> None:
        result = guard.evaluate(self.payload("execute_code", {"code": "pass"}))
        self.assertEqual(result["action"], "block")

    def test_allows_execute_code_outside_workspace_context(self) -> None:
        result = guard.evaluate(
            self.payload(
                "execute_code",
                {"code": "pass"},
                cwd=r"D:\external-project",
            )
        )
        self.assertEqual(result, {})

    def test_blocks_process_tool(self) -> None:
        result = guard.evaluate(self.payload("process", {"action": "start"}))
        self.assertEqual(result["action"], "block")

    def test_blocks_mutating_mcp_without_path(self) -> None:
        result = guard.evaluate(
            self.payload("mcp_filesystem_move_file", {})
        )
        self.assertEqual(result["action"], "block")
        self.assertIn("failed closed", result["message"])

    def test_allows_read_only_mcp_action_on_workspace_document(self) -> None:
        result = guard.evaluate(
            self.payload(
                "mcp_wps_agent_content",
                {
                    "action": "full_text",
                    "filepath": r"${WORKSPACE_ROOT}\README.md",
                },
            )
        )
        self.assertEqual(result, {})

    def test_blocks_mutating_mcp_action_on_workspace_document(self) -> None:
        result = guard.evaluate(
            self.payload(
                "mcp_wps_agent_content",
                {
                    "action": "replace_range",
                    "filepath": r"${WORKSPACE_ROOT}\README.md",
                },
            )
        )
        self.assertEqual(result["action"], "block")

    def test_allows_mutating_mcp_action_with_external_output_path(self) -> None:
        result = guard.evaluate(
            self.payload(
                "mcp_wps_agent_offline_docx",
                {
                    "action": "build",
                    "output_path": r"${WORKSPACE_ROOT}\out\hermes\document.docx",
                },
            )
        )
        self.assertEqual(result, {})

    def test_windows_paths_keep_meaning_under_posix_runner(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(guard, "STATE_ROOT", Path(temporary)),
            patch.object(
                guard,
                "WORKSPACE_ROOT",
                PurePosixPath("/home/runner/work/workspace/workspace"),
            ),
        ):
            guard.evaluate(
                self.payload(
                    "skill_view",
                    {"name": "style-doctor"},
                    event="post_tool_call",
                )
            )
            diagnosis = guard.evaluate(
                self.payload(
                    "write_file",
                    {
                        "path": (
                            r"${WORKSPACE_ROOT}\packages\character-system"
                            r"\reports\runtime-loop\diagnoses\DIAG-demo.md"
                        )
                    },
                )
            )
            external = guard.evaluate(
                self.payload(
                    "mcp_wps_agent_offline_docx",
                    {
                        "action": "build",
                        "output_path": r"${WORKSPACE_ROOT}\out\hermes\document.docx",
                    },
                )
            )
        self.assertEqual(diagnosis, {})
        self.assertEqual(external, {})

    def test_blocks_mutating_mcp_action_with_only_document_id(self) -> None:
        result = guard.evaluate(
            self.payload(
                "mcp_wps_agent_content",
                {"action": "insert_text", "doc_id": "doc-1"},
            )
        )
        self.assertEqual(result["action"], "block")
        self.assertIn("failed closed", result["message"])

    def test_records_active_skill_and_injects_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                guard.evaluate(
                    self.payload(
                        "skill_view",
                        {"name": "zyc"},
                        event="post_tool_call",
                    )
                )
                result = guard.evaluate(
                    self.payload("", {}, event="pre_llm_call")
                )
        self.assertIn("Active skill: zyc", result["context"])
        self.assertIn("record_producer", result["context"])
        self.assertIn("never offer", result["context"])
        self.assertIn("read-only filesystem MCP", result["context"])

    def test_does_not_inject_workspace_context_for_external_work(self) -> None:
        result = guard.evaluate(
            self.payload(
                "",
                {},
                event="pre_llm_call",
                cwd=r"D:\external-project",
            )
        )
        self.assertEqual(result, {})

    def test_runtime_skill_cannot_write_diagnosis_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                guard.evaluate(
                    self.payload(
                        "skill_view",
                        {"name": "zyc"},
                        event="post_tool_call",
                    )
                )
                result = guard.evaluate(
                    self.payload(
                        "write_file",
                        {
                            "path": (
                                r"${WORKSPACE_ROOT}\packages\character-system"
                                r"\reports\runtime-loop\diagnoses\DIAG-demo.md"
                            )
                        },
                    )
                )
        self.assertEqual(result["action"], "block")
        self.assertIn("does not permit record_write", result["message"])

    def test_style_doctor_can_write_diagnosis_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(guard, "STATE_ROOT", Path(temporary)):
                guard.evaluate(
                    self.payload(
                        "skill_view",
                        {"name": "style-doctor"},
                        event="post_tool_call",
                    )
                )
                result = guard.evaluate(
                    self.payload(
                        "write_file",
                        {
                            "path": (
                                r"${WORKSPACE_ROOT}\packages\character-system"
                                r"\reports\runtime-loop\diagnoses\DIAG-demo.md"
                            )
                        },
                    )
                )
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
