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
        self.assertEqual(payload["enabled"], True)
        self.assertTrue(payload["toggle_file"])
        self.assertTrue(payload["hook_honors_toggle"])
        self.assertTrue(payload["settings_mentions_hook"])
        self.assertTrue(payload["claude_mentions_toggle"])
        self.assertTrue(payload["policy_mentions_toggle"])
        self.assertTrue(payload["integration_installed"])

    def test_off_and_on_write_only_toggle_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            off = self.run_script("off", "--project-root", str(root), "--format", "json")
            self.assertEqual(off.returncode, 0, off.stderr)
            off_payload = json.loads(off.stdout)
            self.assertEqual(off_payload["enabled"], False)
            toggle = root / ".claude" / "model-routing-advice.json"
            self.assertEqual(json.loads(toggle.read_text(encoding="utf-8"))["enabled"], False)

            on = self.run_script("on", "--project-root", str(root), "--format", "json")
            self.assertEqual(on.returncode, 0, on.stderr)
            on_payload = json.loads(on.stdout)
            self.assertEqual(on_payload["enabled"], True)
            self.assertEqual(json.loads(toggle.read_text(encoding="utf-8"))["enabled"], True)

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
                'function Test-ModelAdviceEnabled() { ".claude\\model-routing-advice.json" }',
                encoding="utf-8",
            )
            status = project_status(root)
        self.assertEqual(status["enabled"], False)
        self.assertTrue(status["hook_honors_toggle"])
        self.assertTrue(status["disabled_is_clean"])


if __name__ == "__main__":
    unittest.main()
