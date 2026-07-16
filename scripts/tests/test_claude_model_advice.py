from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.claude_model_advice import WORKSPACE_ROOT, project_status


SCRIPT = WORKSPACE_ROOT / "scripts" / "claude_model_advice.py"


class ClaudeModelAdviceTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_status_reports_workspace_integration(self) -> None:
        result = self.run_script("status", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload["enabled"], bool)
        self.assertTrue(payload["toggle_file"])
        self.assertTrue(payload["hook_honors_toggle"])
        self.assertTrue(payload["settings_mentions_hook"])
        self.assertTrue(payload["claude_mentions_toggle"])
        self.assertFalse(payload["claude_imports_policy"])
        self.assertFalse(payload["claude_static_markers"])
        self.assertTrue(payload["static_prompt_layer_clean"])
        self.assertTrue(payload["policy_mentions_toggle"])
        self.assertTrue(payload["integration_installed"])
        self.assertIn(payload["runtime_enforcement"], {"enabled", "disabled"})
        self.assertEqual(payload["will_inject_or_block"], payload["enabled"])

    def test_off_and_on_write_only_toggle_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            off = self.run_script("off", "--project-root", str(root), "--format", "json")
            self.assertEqual(off.returncode, 0, off.stderr)
            off_payload = json.loads(off.stdout)
            self.assertEqual(off_payload["enabled"], False)
            self.assertEqual(off_payload["runtime_enforcement"], "unavailable")
            self.assertFalse(off_payload["will_inject_or_block"])
            local_toggle = root / ".claude" / "model-routing-advice.local.json"
            tracked_toggle = root / ".claude" / "model-routing-advice.json"
            self.assertEqual(json.loads(local_toggle.read_text(encoding="utf-8"))["enabled"], False)
            self.assertFalse(tracked_toggle.exists())

            on = self.run_script("on", "--project-root", str(root), "--format", "json")
            self.assertEqual(on.returncode, 0, on.stderr)
            on_payload = json.loads(on.stdout)
            self.assertEqual(on_payload["enabled"], True)
            self.assertEqual(on_payload["runtime_enforcement"], "unavailable")
            self.assertEqual(json.loads(local_toggle.read_text(encoding="utf-8"))["enabled"], True)

    def test_tracked_scope_updates_project_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.run_script(
                "off",
                "--project-root",
                str(root),
                "--scope",
                "tracked",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            tracked_toggle = root / ".claude" / "model-routing-advice.json"
            local_toggle = root / ".claude" / "model-routing-advice.local.json"
            self.assertEqual(json.loads(tracked_toggle.read_text(encoding="utf-8"))["enabled"], False)
            self.assertFalse(local_toggle.exists())

    def test_external_project_status_exposes_missing_integration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.run_script("on", "--project-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
        self.assertEqual(payload["enabled"], True)
        self.assertFalse(payload["integration_installed"])
        self.assertFalse(payload["hook_file"])
        self.assertIn("--project-root <git-root>", " ".join(payload["external_interface"]["commands"]))

    def test_project_status_treats_disabled_hook_as_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".claude" / "hooks").mkdir(parents=True)
            (root / ".claude" / "settings.json").write_text("model_routing_guard.ps1", encoding="utf-8")
            (root / ".claude" / "model-routing-advice.json").write_text(
                json.dumps({"interface_version": 1, "enabled": False}),
                encoding="utf-8",
            )
            (root / ".claude" / "hooks" / "model_routing_guard.ps1").write_text(
                (
                    'function Test-ModelAdviceEnabled() { '
                    '".claude\\model-routing-advice.local.json"; '
                    '".claude\\model-routing-advice.json" }'
                ),
                encoding="utf-8",
            )
            status = project_status(root)
        self.assertEqual(status["enabled"], False)
        self.assertTrue(status["hook_honors_toggle"])
        self.assertTrue(status["disabled_is_clean"])

    def test_status_text_separates_installed_from_runtime_enforcement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".claude" / "hooks").mkdir(parents=True)
            (root / ".claude" / "settings.json").write_text("model_routing_guard.ps1", encoding="utf-8")
            (root / ".claude" / "model-routing-advice.json").write_text(
                json.dumps({"interface_version": 1, "enabled": False}),
                encoding="utf-8",
            )
            (root / ".claude" / "hooks" / "model_routing_guard.ps1").write_text(
                (
                    'function Test-ModelAdviceEnabled() { '
                    '".claude\\model-routing-advice.local.json"; '
                    '".claude\\model-routing-advice.json" }'
                ),
                encoding="utf-8",
            )
            (root / "CLAUDE.md").write_text(".claude/model-routing-advice.json", encoding="utf-8")
            policy = root / "shared" / "claude" / "policies" / "model-routing-policy.md"
            policy.parent.mkdir(parents=True)
            policy.write_text(".claude/model-routing-advice.json", encoding="utf-8")

            result = self.run_script("status", "--project-root", str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Claude model advice: OFF", result.stdout)
        self.assertIn("Runtime enforcement: disabled (will not inject or block)", result.stdout)
        self.assertIn("Source: tracked default", result.stdout)
        self.assertIn("Tracked default: OFF", result.stdout)
        self.assertIn("Local override: not set", result.stdout)
        self.assertIn("static CLAUDE.md prompt layer: disabled", result.stdout)
        self.assertIn("CLAUDE.md avoids static routing template: yes", result.stdout)
        self.assertIn("Installed: yes", result.stdout)

    def test_local_override_takes_precedence_over_tracked_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".claude").mkdir(parents=True)
            (root / ".claude" / "model-routing-advice.json").write_text(
                json.dumps({"interface_version": 1, "enabled": True}),
                encoding="utf-8",
            )
            (root / ".claude" / "model-routing-advice.local.json").write_text(
                json.dumps({"interface_version": 1, "enabled": False}),
                encoding="utf-8",
            )
            status = project_status(root)
        self.assertEqual(status["enabled"], False)
        self.assertEqual(status["tracked_enabled"], True)
        self.assertEqual(status["local_enabled"], False)
        self.assertEqual(status["toggle_source"], "local override")

    def test_static_claude_routing_template_prevents_fully_off_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".claude" / "hooks").mkdir(parents=True)
            (root / ".claude" / "settings.json").write_text("model_routing_guard.ps1", encoding="utf-8")
            (root / ".claude" / "model-routing-advice.json").write_text(
                json.dumps({"interface_version": 1, "enabled": False}),
                encoding="utf-8",
            )
            (root / ".claude" / "hooks" / "model_routing_guard.ps1").write_text(
                (
                    'function Test-ModelAdviceEnabled() { '
                    '".claude\\model-routing-advice.local.json"; '
                    '".claude\\model-routing-advice.json" }'
                ),
                encoding="utf-8",
            )
            (root / "CLAUDE.md").write_text(
                ".claude/model-routing-advice.json\nRecommend Pro",
                encoding="utf-8",
            )
            policy = root / "shared" / "claude" / "policies" / "model-routing-policy.md"
            policy.parent.mkdir(parents=True)
            policy.write_text(".claude/model-routing-advice.json", encoding="utf-8")
            status = project_status(root)
        self.assertEqual(status["enabled"], False)
        self.assertFalse(status["static_prompt_layer_clean"])
        self.assertEqual(status["prompt_layer"], "leaking static instructions")
        self.assertFalse(status["fully_disabled"])


if __name__ == "__main__":
    unittest.main()
