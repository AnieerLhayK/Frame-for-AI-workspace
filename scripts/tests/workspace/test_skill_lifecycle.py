from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.workspace.skill_lifecycle import (
    expose_skill,
    init_skill,
    list_skills,
    preview_dsh_skills,
    render_dsh_skill_pointer,
    projection_state,
    validate_skill,
)


class SkillLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.skill_source = self.root / "skills" / "demo"
        self.link_path = self.root / "platform" / "demo"
        self.manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [
                {
                    "id": "demo",
                    "role": "production",
                    "source_path": "skills/demo",
                    "required_files": ["SKILL.md", "README.md"],
                    "exposures": [
                        {
                            "platform": "codex",
                            "projection_id": "codex.demo",
                        }
                    ],
                }
            ],
            "projections": [
                {
                    "id": "codex.demo",
                    "platform": "codex",
                    "link_path": str(self.link_path),
                    "target_path": "skills/demo",
                }
            ],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_valid_skill(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: portable\n  distribution: review-required\n  requires: [python]\n"
            "---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

    def test_init_creates_bounded_source_scaffold(self) -> None:
        manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [],
            "projections": [],
        }
        result = init_skill(
            manifest,
            "new-skill",
            "skills/new-skill",
            "A new test skill.",
        )

        self.assertEqual(result["status"], "CREATED")
        source = self.root / "skills" / "new-skill"
        self.assertTrue((source / "SKILL.md").is_file())
        self.assertTrue((source / "references" / "README.md").is_file())
        self.assertIn("name: new-skill", (source / "SKILL.md").read_text(encoding="utf-8"))

    def test_init_refuses_path_outside_workspace(self) -> None:
        manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [],
            "projections": [],
        }
        result = init_skill(
            manifest,
            "new-skill",
            "../outside",
            "A new test skill.",
        )
        self.assertEqual(result["status"], "BLOCKED")

    def test_validate_registered_skill(self) -> None:
        self.create_valid_skill()
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["registered"])

    def test_ignored_local_bytecode_passes_but_tracked_bytecode_fails(self) -> None:
        self.create_valid_skill()
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        (self.root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        cache = self.skill_source / "scripts" / "__pycache__" / "demo.pyc"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"cache")

        self.assertEqual(validate_skill(self.manifest, "demo")["status"], "PASS")

        subprocess.run(
            ["git", "add", "-f", "--", str(cache)],
            cwd=self.root, check=True, capture_output=True,
        )
        findings = validate_skill(self.manifest, "demo")["findings"]
        self.assertTrue(any("demo.pyc" in finding for finding in findings))

    def test_ignored_reports_still_fail_validation(self) -> None:
        self.create_valid_skill()
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        (self.root / ".gitignore").write_text("reports/\n", encoding="utf-8")
        report = self.skill_source / "reports" / "run.log"
        report.parent.mkdir()
        report.write_text("runtime output", encoding="utf-8")

        findings = validate_skill(self.manifest, "demo")["findings"]
        self.assertTrue(any("reports/run.log" in finding for finding in findings))

    def test_validate_registered_skill_without_unrequired_readme(self) -> None:
        self.create_valid_skill()
        (self.skill_source / "README.md").unlink()
        self.manifest["skills"][0]["required_files"] = ["SKILL.md"]
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS")

    def test_validate_accepts_registered_source_path(self) -> None:
        self.create_valid_skill()
        result = validate_skill(self.manifest, "skills/demo")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["skill_id"], "demo")

    def test_validate_reports_frontmatter_name_mismatch(self) -> None:
        self.create_valid_skill()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: wrong\ndescription: Demo skill.\n---\n",
            encoding="utf-8",
        )
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("frontmatter name", result["findings"][0])

    def test_validate_enhanced_contract_and_invocation_mirror(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\ndisable-model-invocation: true\n"
            "metadata:\n  portability: portable\n  distribution: review-required\n"
            "  requires: [python]\n---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "interface:\n  display_name: Demo\npolicy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS")

    def test_validate_rejects_non_boolean_invocation_flag(self) -> None:
        self.create_valid_skill()
        skill = self.skill_source / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        skill.write_text(content.replace("description: Demo skill.",
            'description: Demo skill.\ndisable-model-invocation: "true"'), encoding="utf-8")
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("disable-model-invocation must be a boolean", "\n".join(result["findings"]))

    def test_registered_package_skill_accepts_owned_maintenance_reports(self) -> None:
        self.skill_source = self.root / "packages" / "demo"
        self.manifest["skills"][0]["source_path"] = "packages/demo"
        self.manifest["skills"][0]["optional_files"] = ["reports"]
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n  hermes:\n    related_skills: []\n---\n",
            encoding="utf-8")
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")
        (self.skill_source / "reports").mkdir()
        (self.skill_source / "reports" / "maintenance.md").write_text("# Maintenance\n", encoding="utf-8")
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS", result["findings"])
        nested = self.skill_source / "scripts" / "reports"
        nested.mkdir(parents=True)
        (nested / "runtime.log").write_text("runtime output", encoding="utf-8")
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("runtime artifacts", "\n".join(result["findings"]))

    def test_validate_rejects_invocation_drift_and_runtime_artifacts(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "scripts" / "__pycache__").mkdir(parents=True)
        (self.skill_source / "scripts" / "__pycache__" / "demo.pyc").write_bytes(b"cache")
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n"
            "metadata:\n  portability: portable\n  distribution: review-required\n"
            "  requires: [python]\n---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
        (self.skill_source / "README.md").write_text("[missing](nope.md)\n", encoding="utf-8")
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "ERROR")
        joined = "\n".join(result["findings"])
        self.assertIn("must mirror", joined)
        self.assertIn("runtime artifacts", joined)
        self.assertIn("broken local Markdown link", joined)

    def test_metadata_absence_does_not_bypass_general_package_checks(self) -> None:
        self.create_valid_skill()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("[missing](nope.md)\n", encoding="utf-8")
        (self.skill_source / "scripts" / "__pycache__").mkdir(parents=True)
        (self.skill_source / "scripts" / "__pycache__" / "demo.pyc").write_bytes(b"cache")

        result = validate_skill(self.manifest, "demo")

        joined = "\n".join(result["findings"])
        self.assertIn("standalone skill requires frontmatter metadata", joined)
        self.assertIn("must mirror", joined)
        self.assertIn("broken local Markdown link", joined)
        self.assertIn("runtime artifacts", joined)

    def test_metadata_contract_requires_openai_policy_file(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: portable\n  distribution: review-required\n  requires: [python]\n"
            "---\n",
            encoding="utf-8",
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

        result = validate_skill(self.manifest, "demo")

        self.assertIn("missing required file: agents/openai.yaml", result["findings"])

    def test_portable_host_coupling_scans_runtime_not_reference_examples(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "scripts").mkdir()
        (self.skill_source / "references").mkdir()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: portable\n  distribution: review-required\n  requires: [python, windows]\n"
            "---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (self.skill_source / "scripts" / "run.py").write_text(
            'ROOT = "E:\\\\Work\\\\runtime"\n', encoding="utf-8"
        )
        (self.skill_source / "references" / "example.md").write_text(
            "workspace records start --example\n", encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

        result = validate_skill(self.manifest, "demo")

        joined = "\n".join(result["findings"])
        self.assertIn("portable skill cannot require host capabilities: windows", joined)
        self.assertIn("portable skill contains host coupling in runtime surfaces: windows-path", joined)
        self.assertNotIn("workspace-cli", joined)

    def test_workspace_bound_runtime_requires_workspace_cli_metadata(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "config").mkdir()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: workspace-bound\n  distribution: review-required\n  requires: [python, host-write-authorization]\n"
            "---\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (self.skill_source / "config" / "runtime.yaml").write_text(
            "command: workspace records start --task-type demo\n", encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

        result = validate_skill(self.manifest, "demo")

        self.assertIn(
            "Workspace CLI coupling requires metadata.requires to include workspace-cli",
            result["findings"],
        )

    def test_host_adapted_windows_runtime_requires_windows_metadata(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "scripts").mkdir()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: host-adapted\n  distribution: review-required\n"
            "  requires: [python, host-write-authorization]\n---\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (self.skill_source / "scripts" / "run.ps1").write_text(
            "$root = 'E:/Work/runtime'\n", encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

        result = validate_skill(self.manifest, "demo")

        self.assertIn(
            "Windows path coupling requires metadata.requires to include windows or windows-powershell",
            result["findings"],
        )

    def test_optional_manifest_fallback_is_not_a_workspace_cli_dependency(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "agents").mkdir()
        (self.skill_source / "scripts").mkdir()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\nmetadata:\n"
            "  portability: host-adapted\n  distribution: review-required\n"
            "  requires: [python, windows, optional-workspace-manifest]\n---\n",
            encoding="utf-8",
        )
        (self.skill_source / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (self.skill_source / "scripts" / "output_paths.py").write_text(
            'DEFAULT_MANIFEST = "workspace_manifest.yaml"\n', encoding="utf-8"
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

        result = validate_skill(self.manifest, "demo")

        self.assertEqual(result["status"], "PASS")

    def test_python_detector_constants_do_not_count_as_runtime_host_paths(self) -> None:
        self.create_valid_skill()
        (self.skill_source / "scripts").mkdir()
        (self.skill_source / "scripts" / "scanner.py").write_text(
            "import re\n"
            'RESIDUAL_MARKERS = ("E:/Work/runtime", "workspace_manifest.yaml")\n'
            'RESIDUAL_PATTERNS = ("workspace records",)\n'
            'HOST_PATTERN = re.compile(r"E:/Work/runtime")\n',
            encoding="utf-8",
        )

        result = validate_skill(self.manifest, "demo")

        self.assertEqual(result["status"], "PASS")

    def test_list_reports_source_and_projection_state(self) -> None:
        self.create_valid_skill()
        result = list_skills(self.manifest)
        self.assertEqual(result["skills"][0]["source_state"], "OK")
        self.assertEqual(result["skills"][0]["projections"][0]["state"], "MISSING")

    def test_projection_state_detects_broken_or_incorrect_link(self) -> None:
        self.create_valid_skill()
        with (
            patch("scripts.workspace.skill_lifecycle.os.path.lexists", return_value=True),
            patch(
                "scripts.workspace.skill_lifecycle.os.path.realpath",
                return_value=str(self.root / "old-target"),
            ),
        ):
            state = projection_state(self.link_path, self.skill_source)
        self.assertEqual(state, "BLOCKED_EXISTING_ITEM")

    def test_expose_defaults_to_plan_without_writing(self) -> None:
        self.create_valid_skill()
        result = expose_skill(self.manifest, "demo", "codex")
        self.assertEqual(result["status"], "PLAN")
        self.assertFalse(self.link_path.exists())

    def test_expose_apply_uses_selected_projection_creator(self) -> None:
        self.create_valid_skill()
        calls: list[tuple[Path, Path]] = []

        def creator(link: Path, target: Path) -> None:
            calls.append((link, target))

        result = expose_skill(
            self.manifest,
            "demo",
            "codex",
            apply=True,
            creator=creator,
        )
        self.assertEqual(result["status"], "CREATED")
        self.assertEqual(calls, [(self.link_path.resolve(), self.skill_source.resolve())])

    def test_expose_preserves_existing_real_directory(self) -> None:
        self.create_valid_skill()
        self.link_path.mkdir(parents=True)
        result = expose_skill(
            self.manifest,
            "demo",
            "codex",
            apply=True,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(self.link_path.is_dir())

    def test_dsh_preview_lists_only_approved_skills_without_enabling_them(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: A demo.\ndisable-model-invocation: true\n---\n", encoding="utf-8"
        )
        dependency = self.root / "skills" / "grilling"
        dependency.mkdir(parents=True)
        (dependency / "SKILL.md").write_text("---\nname: grilling\ndescription: Dependency.\n---\n", encoding="utf-8")
        self.manifest["skills"].append({"id": "grilling", "source_path": "skills/grilling"})
        catalog = self.root / "catalog.yaml"
        catalog.write_text("schema_version: 1\nskills:\n  - {id: demo, trigger: automatic}\n  - {id: grilling, trigger: dependency_only}\n", encoding="utf-8")
        payload = preview_dsh_skills(self.manifest, catalog)
        rows = {row["id"]: row for row in payload["skills"]}
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows["demo"]["trigger"], "automatic")
        self.assertEqual(rows["grilling"]["trigger"], "dependency_only")
        self.assertEqual(rows["demo"]["state"], "adaptation_required")
        self.assertNotIn("showcase-packer", rows)
        self.assertNotIn("putogether", rows)
        self.assertFalse(payload["activation_performed"])

    def test_dsh_pointer_preserves_source_and_explicit_trigger(self) -> None:
        row = {"id": "demo", "trigger": "explicit", "source_path": "skills/demo", "description": "Demo trigger."}
        pointer = render_dsh_skill_pointer(row, self.root)
        self.assertIn("disable-model-invocation: true", pointer)
        self.assertIn(str(self.root / "skills/demo/SKILL.md").replace('\\', '/'), pointer)

    def test_dsh_pointer_explains_owner_approved_invocation_adaptation(self) -> None:
        row = {"id": "demo", "trigger": "automatic", "source_path": "skills/demo",
               "description": "Use for accessible responses.", "adaptation_note": "Owner approved automatic discovery despite the source's explicit invocation setting."}
        pointer = render_dsh_skill_pointer(row, self.root)
        self.assertIn("disable-model-invocation: false", pointer)
        self.assertIn(row["adaptation_note"], pointer)

    def test_dsh_pointer_rejects_internal_dependency_and_escape(self) -> None:
        with self.assertRaises(ValueError):
            render_dsh_skill_pointer({"id": "demo", "trigger": "dependency_only", "source_path": "skills/demo"}, self.root)
        with self.assertRaises(ValueError):
            render_dsh_skill_pointer({"id": "demo", "trigger": "automatic", "source_path": "../private"}, self.root)

    def test_dsh_preview_rejects_unregistered_source(self) -> None:
        catalog = self.root / "catalog.yaml"
        catalog.write_text("schema_version: 1\nskills:\n  - {id: unknown, trigger: automatic, source_path: skills/demo}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unregistered DSH skill is not approved"):
            preview_dsh_skills(self.manifest, catalog)

    def test_dsh_preview_records_explicit_invocation_adaptation(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / 'SKILL.md').write_text('---\nname: demo\ndescription: Invoke explicitly.\ndisable-model-invocation: true\n---\n', encoding='utf-8')
        catalog = self.root / 'catalog.yaml'
        catalog.write_text('schema_version: 1\nskills:\n  - id: demo\n    trigger: automatic\n    description_override: Accessible output.\n    adaptation_note: Owner approved automatic discovery.\n', encoding='utf-8')
        row = preview_dsh_skills(self.manifest, catalog)['skills'][0]
        self.assertEqual(row['state'], 'adaptation_ready_for_verification')
        self.assertEqual(row['description'], 'Accessible output.')
        self.assertIn('Owner approved', row['adaptation_note'])

    def test_dsh_preview_reports_invalid_catalog(self) -> None:
        catalog = self.root / "catalog.yaml"
        catalog.write_text("schema_version: [", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid DSH skill catalog"):
            preview_dsh_skills(self.manifest, catalog)

    def test_dsh_preview_reports_missing_private_catalog(self) -> None:
        with self.assertRaisesRegex(ValueError, "DSH skill catalog is not configured"):
            preview_dsh_skills(self.manifest, self.root / "missing.yaml")

    def test_dsh_preview_marks_approved_unregistered_skill_for_registration(self) -> None:
        source = self.root / "packages/character-system/engineering/generation/character-generator/characters/test-character"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("---\nname: test-character\ndescription: Style.\n---\n", encoding="utf-8")
        catalog = self.root / "catalog.yaml"
        catalog.write_text("schema_version: 1\nskills:\n  - {id: test-character, trigger: explicit, approved_unregistered: true, source_path: packages/character-system/engineering/generation/character-generator/characters/test-character}\n", encoding="utf-8")
        result = preview_dsh_skills(self.manifest, catalog)
        self.assertEqual(result["skills"][0]["state"], "registration_required")
        self.assertFalse(result["activation_performed"])


if __name__ == "__main__":
    unittest.main()
