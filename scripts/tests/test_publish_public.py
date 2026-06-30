import tempfile
import unittest
import os
import stat
from pathlib import Path

from scripts.publish_check import (
    EXPECTED_DOCS,
    REQUIRED_PATHS,
    check_forbidden_paths,
    run_functional_checks,
    run_tests,
)
from scripts.publish_public import (
    SCRUB_FILES,
    generate_beginner_guide_md,
    generate_onboarding_md,
    generate_public_setup_py,
    scrub_content,
)
from scripts.sync_public_repo import cleanup_staging


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

    def test_workspace_cli_tests_are_scrubbed_for_public_release(self) -> None:
        self.assertIn("scripts/tests/test_workspace_cli.py", SCRUB_FILES)

    def test_public_beginner_guide_mentions_setup_and_explain(self) -> None:
        guide = generate_beginner_guide_md("Frame-for-AI-workspace")
        self.assertIn("scripts/setup_public_workspace.py", guide)
        self.assertIn("workspace_cli.py explain mechanism task-routing", guide)
        self.assertIn("does not configure provider credentials", guide)

    def test_public_setup_script_is_conservative(self) -> None:
        script = generate_public_setup_py()
        self.assertIn("TEMPLATE_FILES", script)
        self.assertIn("explain\", \"mechanism\", \"task-routing", script)
        self.assertIn("updated-placeholders", script)
        self.assertIn("as_posix()", script)
        self.assertIn("Provider credentials", script)
        self.assertNotIn("git push", script)

    def test_onboarding_points_beginners_to_setup_script(self) -> None:
        onboarding = generate_onboarding_md("Frame-for-AI-workspace")
        self.assertIn("BEGINNER_GUIDE.md", onboarding)
        self.assertIn("scripts/setup_public_workspace.py", onboarding)
        self.assertIn("workspace_cli.py explain path scripts/workspace_cli.py", onboarding)

    def test_publish_check_requires_beginner_setup_assets(self) -> None:
        self.assertIn("BEGINNER_GUIDE.md", EXPECTED_DOCS)
        self.assertIn("scripts/setup_public_workspace.py", REQUIRED_PATHS)

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

    def test_public_sync_cleans_managed_staging_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            managed = Path(tmp) / "Frame-for-AI-workspace"
            managed.mkdir()
            marker = managed / "marker.txt"
            marker.write_text("temporary", encoding="utf-8")
            marker.chmod(stat.S_IREAD)

            import scripts.sync_public_repo as sync_public_repo

            original = sync_public_repo.DEFAULT_STAGING_ROOT
            sync_public_repo.DEFAULT_STAGING_ROOT = Path(tmp)
            try:
                cleanup_staging(str(managed))
            finally:
                sync_public_repo.DEFAULT_STAGING_ROOT = original
                if marker.exists():
                    os.chmod(marker, stat.S_IWRITE)

            self.assertFalse(managed.exists())

    def test_public_sync_does_not_remove_custom_staging_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom-public-checkout"
            custom.mkdir()

            cleanup_staging(str(custom))

            self.assertTrue(custom.exists())


if __name__ == "__main__":
    unittest.main()
