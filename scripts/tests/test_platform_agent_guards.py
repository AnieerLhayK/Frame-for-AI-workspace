from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
AGENT_GOVERNANCE = WORKSPACE_ROOT / "scripts" / "agent_governance.py"
OPENCODE_GUARD = (
    WORKSPACE_ROOT / ".opencode" / "plugins" / "workspace-governance.js"
)


class PlatformAgentAuthorizationTests(unittest.TestCase):
    def check_access(self, agent: str, skill: str, path: str) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                str(AGENT_GOVERNANCE),
                "check",
                "--agent",
                agent,
                "--skill",
                skill,
                "--path",
                path,
                "--format",
                "json",
            ],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertIn(result.returncode, (0, 2), result.stderr)
        return json.loads(result.stdout)

    def test_reasonix_and_opencode_cannot_patch_zyc_source(self) -> None:
        target = (
            "packages/character-system/runtime/characters/zyc/"
            "references/voice_card.md"
        )
        for agent in ("reasonix", "opencode"):
            with self.subTest(agent=agent):
                payload = self.check_access(agent, "zyc", target)
                self.assertEqual(payload["status"], "DENY")

    def test_reasonix_and_opencode_can_write_style_doctor_diagnosis(self) -> None:
        target = (
            "packages/character-system/reports/runtime-loop/"
            "diagnoses/DIAG-platform-test.md"
        )
        for agent in ("reasonix", "opencode"):
            with self.subTest(agent=agent):
                payload = self.check_access(agent, "style-doctor", target)
                self.assertEqual(payload["status"], "ALLOW")

    def test_cursor_remains_consumer(self) -> None:
        denied = self.check_access(
            "cursor",
            "zyc",
            "packages/character-system/runtime/characters/zyc/SKILL.md",
        )
        allowed = self.check_access(
            "cursor",
            "zyc",
            "reports/agent-requests/REQ-cursor-test.md",
        )
        self.assertEqual(denied["status"], "DENY")
        self.assertEqual(allowed["status"], "ALLOW")


@unittest.skipUnless(shutil.which("node"), "OpenCode guard tests require Node.js.")
class OpenCodeGuardTests(unittest.TestCase):
    def run_guard_case(self, case: str) -> subprocess.CompletedProcess[str]:
        script = f"""
import {{ WorkspaceGovernance }} from {json.dumps(OPENCODE_GUARD.as_uri())};
const hooks = await WorkspaceGovernance({{ directory: {json.dumps(str(WORKSPACE_ROOT))} }});
const before = hooks["tool.execute.before"];
const transform = hooks["experimental.chat.system.transform"];
if ({json.dumps(case)} === "prompt") {{
  const output = {{ system: [] }};
  await transform({{}}, output);
  if (!output.system.join(" ").includes("User approval does not expand authority")) process.exit(4);
}} else if ({json.dumps(case)} === "read-shell") {{
  await before({{ tool: "bash", sessionID: "s1" }}, {{ args: {{ command: "git status --short" }} }});
}} else if ({json.dumps(case)} === "write-shell") {{
  await before({{ tool: "bash", sessionID: "s1" }}, {{ args: {{ command: "git commit -am test" }} }});
}} else if ({json.dumps(case)} === "source") {{
  await before({{ tool: "skill", sessionID: "s1" }}, {{ args: {{ name: "zyc" }} }});
  await before({{ tool: "edit", sessionID: "s1" }}, {{ args: {{ filePath: "packages/character-system/runtime/characters/zyc/SKILL.md" }} }});
}} else if ({json.dumps(case)} === "diagnosis") {{
  await before({{ tool: "skill", sessionID: "s1" }}, {{ args: {{ name: "style-doctor" }} }});
  await before({{ tool: "edit", sessionID: "s1" }}, {{ args: {{ filePath: "packages/character-system/reports/runtime-loop/diagnoses/DIAG-test.md" }} }});
}} else if ({json.dumps(case)} === "diagnosis-no-skill") {{
  await before({{ tool: "edit", sessionID: "s2" }}, {{ args: {{ filePath: "packages/character-system/reports/runtime-loop/diagnoses/DIAG-test.md" }} }});
}}
"""
        return subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_cognitive_contract_is_injected(self) -> None:
        result = self.run_guard_case("prompt")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_read_only_shell_is_allowed(self) -> None:
        result = self.run_guard_case("read-shell")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mutating_shell_is_blocked(self) -> None:
        result = self.run_guard_case("write-shell")
        self.assertNotEqual(result.returncode, 0)

    def test_zyc_source_edit_is_blocked(self) -> None:
        result = self.run_guard_case("source")
        self.assertNotEqual(result.returncode, 0)

    def test_style_doctor_diagnosis_is_allowed(self) -> None:
        result = self.run_guard_case("diagnosis")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_runtime_record_requires_active_skill(self) -> None:
        result = self.run_guard_case("diagnosis-no-skill")
        self.assertNotEqual(result.returncode, 0)
