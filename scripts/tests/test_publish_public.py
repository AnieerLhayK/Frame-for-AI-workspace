import tempfile
import unittest
import os
import stat
from pathlib import Path

from scripts.publish_check import (
    EXPECTED_DOCS,
    REQUIRED_EXTENSION_LAYER_FILES,
    REQUIRED_PATHS,
    check_extension_layers,
    check_forbidden_paths,
    run_functional_checks,
    run_tests,
)
from scripts.publish_public import (
    EXCLUDED_PATHS,
    SCRUB_FILES,
    EXTENSION_LAYER_READMES,
    generate_beginner_guide_md,
    generate_public_manifest,
    generate_public_readme,
    generate_onboarding_md,
    generate_public_setup_py,
    scrub_content,
)
from scripts.sync_public_repo import cleanup_staging
from scripts import sync_public_repo


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

    def test_public_release_excludes_claude_local_settings(self) -> None:
        self.assertIn(".claude/settings.local.json", EXCLUDED_PATHS)

    def test_public_frame_excludes_character_system_and_keeps_documented_skill_layers(self) -> None:
        self.assertIn("packages/character-system", EXCLUDED_PATHS)
        self.assertEqual(
            REQUIRED_EXTENSION_LAYER_FILES,
            {"skills": {"README.md"}, "external-skills": {"README.md"}},
        )
        self.assertIn("does not bundle", EXTENSION_LAYER_READMES["skills"])
        self.assertIn("does not bundle", EXTENSION_LAYER_READMES["external-skills"])

    def test_public_manifest_has_no_private_packages_or_skills(self) -> None:
        manifest = generate_public_manifest(Path("workspace_manifest.yaml"))
        self.assertIn('"packages": []', manifest)
        self.assertIn('"skills": []', manifest)
        self.assertIn('"projections": []', manifest)
        self.assertNotIn('"character-system"', manifest)

    def test_public_readme_states_framework_boundary(self) -> None:
        readme = generate_public_readme("Frame-for-AI-workspace")
        self.assertIn("No `character-system` package is bundled", readme)
        self.assertIn("documentation-only extension", readme)

    def test_extension_layer_check_allows_only_readme_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for layer in REQUIRED_EXTENSION_LAYER_FILES:
                (root / layer).mkdir()
                (root / layer / "README.md").write_text("placeholder\n", encoding="utf-8")

            self.assertEqual(check_extension_layers(root), [])

            (root / "skills" / "SKILL.md").write_text("not allowed\n", encoding="utf-8")
            self.assertIn("skills/", check_extension_layers(root)[0])

    def test_claude_notification_hermes_client_is_scrubbed(self) -> None:
        self.assertIn(
            "scripts/claude_long_task_notifications/hermes-mcp-client.js",
            SCRUB_FILES,
        )

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

    def test_frame_sync_requires_a_task_record(self) -> None:
        with self.assertRaises(SystemExit):
            sync_public_repo.build_parser().parse_args([])


if __name__ == "__main__":
    unittest.main()
