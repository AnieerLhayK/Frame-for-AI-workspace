import tempfile
import unittest
from pathlib import Path

from scripts.publish_check import check_forbidden_paths, run_functional_checks, run_tests
from scripts.publish_public import SCRUB_FILES, scrub_content


AI_ROOT = "D:" + r"\\AI"
USER_ROOT = "C:" + r"\\Users\\Z1377"


class PublicPublishTests(unittest.TestCase):
    def test_scrub_content_replaces_json_escaped_windows_paths(self) -> None:
        text = (
            '{"workspace_root": "' + AI_ROOT + r"\\workspace" + '", '
            '"home": "' + USER_ROOT + r"\\.codex" + '", '
            '"reasonix": "' + AI_ROOT + r"\\data\\reasonix\\cache" + '", '
            '"out": "' + AI_ROOT + r"\\out" + '"}'
        )

        scrubbed = scrub_content(text)

        self.assertNotIn(AI_ROOT, scrubbed)
        self.assertNotIn(USER_ROOT, scrubbed)
        self.assertIn("${WORKSPACE_ROOT}", scrubbed)
        self.assertIn("${USER_HOME}", scrubbed)
        self.assertIn("${DATA_ROOT}/reasonix", scrubbed)
        self.assertIn("${DATA_ROOT}/out", scrubbed)

    def test_publish_check_rejects_json_escaped_windows_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text(
                '{"path": "' + AI_ROOT + r"\\workspace" + '", '
                '"home": "' + USER_ROOT + '"}',
                encoding="utf-8",
            )

            issues = check_forbidden_paths(root)

        self.assertEqual(len(issues), 2)

    def test_reasonix_config_is_scrubbed_for_public_release(self) -> None:
        self.assertIn("reasonix.toml", SCRUB_FILES)

    def test_functional_checks_do_not_leave_routing_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude").mkdir()
            (root / "scripts").mkdir()
            (root / "scripts" / "resolve_task_context.py").write_text(
                "from pathlib import Path\n"
                "Path('.claude/routing_events.ndjson').write_text('event\\n')\n",
                encoding="utf-8",
            )
            (root / "scripts" / "workspace_cli.py").write_text(
                "raise SystemExit(0)\n",
                encoding="utf-8",
            )

            run_functional_checks(root)

            self.assertFalse((root / ".claude" / "routing_events.ndjson").exists())

    def test_pytest_checks_do_not_leave_routing_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude").mkdir()
            tests = root / "scripts" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_event.py").write_text(
                "from pathlib import Path\n\n"
                "def test_event_write():\n"
                "    Path('.claude/routing_events.ndjson').write_text('event\\n')\n",
                encoding="utf-8",
            )

            issues = run_tests(root)

            self.assertEqual(issues, [])
            self.assertFalse((root / ".claude" / "routing_events.ndjson").exists())


if __name__ == "__main__":
    unittest.main()
