from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.workspace.resolve_task_context import (
    TokenCounter,
    budget_status,
    expand_placeholders,
    parse_bindings,
    print_task_list,
    print_text,
    routing_events_path,
    resolve_task,
)


class ResolverTests(unittest.TestCase):
    def test_yaml_context_view_is_emitted_counted_and_refreshed(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT/tasks/registry/index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        task = data["tasks"]["demo"]
        task["required"] = ["workspace_manifest.yaml"]
        task["context_views"] = {"workspace_manifest.yaml": ["workspace"]}
        registry_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        manifest = self.root / "workspace_manifest.yaml"
        manifest.write_text(yaml.safe_dump({"workspace": {"name": "example"}, "unrelated": "x" * 12000}), encoding="utf-8")

        def resolve(optional=False):
            return resolve_task(self.root, "demo", {"target": ["src"]}, optional, True, "missing-test-encoding")

        result = resolve()
        view = result["context"]["required_views"][0]
        self.assertEqual(view["source_path"], "workspace_manifest.yaml")
        self.assertNotIn("workspace_manifest.yaml", result["context"]["required_paths"])
        self.assertEqual(yaml.safe_load(view["content"]), {"workspace": {"name": "example"}})
        self.assertEqual(result["token_budget"]["required_file_tokens"], TokenCounter("missing-test-encoding").count(view["content"]))
        rendered = StringIO()
        with redirect_stdout(rendered):
            print_text(result)
        self.assertIn(view["content"], rendered.getvalue())
        manifest.write_text("workspace: {name: changed}\n", encoding="utf-8")
        self.assertIn("changed", resolve()["context"]["required_views"][0]["content"])
        task["required"] = []
        task["optional"] = ["workspace_manifest.yaml"]
        registry_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        self.assertEqual(resolve()["context"]["optional_views"], [])
        expanded = resolve(True)
        self.assertEqual(expanded["token_budget"]["optional_tokens"], TokenCounter("missing-test-encoding").count(expanded["context"]["optional_views"][0]["content"]))
        manifest.write_text("different: {}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "keys missing"):
            resolve(True)

    def test_routing_events_fallback_uses_workspace_claude_directory(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                routing_events_path(),
                Path(__file__).resolve().parents[3] / ".claude" / "routing_events.ndjson",
            )

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "PROJECT_CONTEXT").mkdir()
        (self.root / "PROJECT_CONTEXT" / "tasks" / "registry").mkdir(parents=True)
        (self.root / "USAGE_GUIDES").mkdir()
        (self.root / "src").mkdir()
        (self.root / "workspace_manifest.yaml").write_text("{}", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("agent rules", encoding="utf-8")
        (self.root / "src" / "target.md").write_text("hello 世界", encoding="utf-8")
        (self.root / "src" / "optional.md").write_text("optional", encoding="utf-8")

        task_registry = {
            "default_rules": {
                "default_ignore": [".git/"],
                "context_budget": {
                    "token_meter": {
                        "encoding": "missing-test-encoding",
                        "required_warn_tokens": 1000,
                        "expanded_warn_tokens": 2000,
                        "hard_max_tokens": None,
                        "max_file_bytes": 2097152,
                        "top_file_count": 5,
                    },
                    "resolver": {
                        "preloaded_files": ["AGENTS.md"],
                        "consumed_files": [
                            "PROJECT_CONTEXT/tasks/registry/index.yaml",
                            "PROJECT_CONTEXT/governance/context_budget.md",
                        ],
                        "retain_consumed_for_tasks": ["registry_edit"],
                    },
                },
                "tool_policy": {
                    "enforcement": "deny_unlisted",
                    "default_profile": "readonly",
                    "profiles": {
                        "readonly": {
                            "allow": ["workspace.read"],
                            "confirm": [],
                            "deny": ["workspace.write"],
                        },
                        "maintenance": {
                            "allow": ["workspace.read", "workspace.write_scoped"],
                            "confirm": ["git.commit"],
                            "deny": ["email"],
                        },
                    },
                },
            },
            "tasks": {
                "demo": {
                    "required": [
                        "PROJECT_CONTEXT/tasks/registry/index.yaml",
                        "<target>/target.md",
                        "git status --short",
                    ],
                    "optional": ["<target>/optional.md"],
                    "ignore": [],
                    "prompt": ["demo_prompt"],
                    "write_scope": ["<target>/target.md"],
                    "validation": ["git diff --check"],
                },
                "registry_edit": {
                    "required": ["PROJECT_CONTEXT/tasks/registry/index.yaml"],
                    "optional": [],
                    "ignore": [],
                    "prompt": ["demo_prompt"],
                    "tool_profile": "maintenance",
                },
            },
        }
        (self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml").write_text(
            yaml.safe_dump(task_registry, sort_keys=False), encoding="utf-8"
        )
        (self.root / "PROJECT_CONTEXT" / "governance").mkdir()
        (self.root / "PROJECT_CONTEXT" / "governance" / "context_budget.md").write_text(
            "budget policy", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_repeated_bindings(self) -> None:
        self.assertEqual(
            parse_bindings(["target=src", "target=other"]),
            {"target": ["src", "other"]},
        )

    def test_task_list_text_is_grouped_table(self) -> None:
        registry = yaml.safe_load(
            (self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml").read_text(
                encoding="utf-8"
            )
        )
        output = StringIO()
        with redirect_stdout(output):
            print_task_list(registry, "text")
        text = output.getvalue()
        self.assertIn("Registered workspace tasks", text)
        self.assertIn("Task id", text)
        self.assertIn("Other", text)
        self.assertIn("demo", text)

    def test_placeholder_expansion_and_unresolved(self) -> None:
        expanded, unresolved = expand_placeholders("<target>/SKILL.md", {"target": ["a", "b"]})
        self.assertEqual(expanded, ["a/SKILL.md", "b/SKILL.md"])
        self.assertFalse(unresolved)
        _, unresolved = expand_placeholders("<missing>/SKILL.md", {})
        self.assertEqual(unresolved, {"missing"})

    def test_resolver_omits_consumed_registry_and_separates_evidence(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertIn("src/target.md", result["context"]["required_paths"])
        self.assertIn(
            "PROJECT_CONTEXT/tasks/registry/index.yaml",
            result["context"]["resolver_consumed_files"],
        )
        self.assertIn("git status --short", result["context"]["external_evidence"])
        self.assertEqual(result["context"]["write_scope"], ["src/target.md"])
        self.assertIsNone(result["token_budget"]["optional_tokens"])
        self.assertFalse(result["token_budget"]["exact"])

    def test_registry_edit_retains_consumed_file(self) -> None:
        result = resolve_task(
            self.root,
            "registry_edit",
            {},
            include_optional=False,
            count_tokens=True,
        )
        self.assertIn(
            "PROJECT_CONTEXT/tasks/registry/index.yaml",
            result["context"]["required_paths"],
        )
        self.assertEqual(result["tool_policy"]["profile"], "maintenance")
        self.assertIn("workspace.write_scoped", result["tool_policy"]["allow"])
        self.assertIn("git.commit", result["tool_policy"]["confirm"])
        self.assertIn("email", result["tool_policy"]["deny"])

    def test_default_tool_policy_denies_unlisted_capabilities(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["tool_policy"]["enforcement"], "deny_unlisted")
        self.assertEqual(result["tool_policy"]["profile"], "readonly")
        self.assertEqual(result["tool_policy"]["allow"], ["workspace.read"])
        self.assertEqual(result["tool_policy"]["deny"], ["workspace.write"])

    def test_unknown_tool_profile_is_rejected(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["tool_profile"] = "missing"
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unknown tool profile"):
            resolve_task(
                self.root,
                "demo",
                {"target": ["src"]},
                include_optional=False,
                count_tokens=True,
            )

    def test_optional_context_is_demand_loaded_without_template_injection(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=True,
            count_tokens=True,
        )
        self.assertGreater(result["token_budget"]["optional_tokens"], 0)
        sources = {item["source"] for item in result["token_budget"]["largest_files"]}
        self.assertIn("optional", sources)
        self.assertNotIn("template", sources)
        self.assertNotIn("prompts", result)
        self.assertNotIn("prompt_frame_tokens", result["token_budget"])
        self.assertNotIn("template_tokens", result["token_budget"])

    def test_unresolved_placeholder_is_reported_without_search(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["context"]["unresolved_placeholders"], ["target"])
        self.assertEqual(result["token_budget"]["required_file_tokens"], 0)
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(
            any("Unresolved required placeholder" in item for item in result["errors"])
        )

    def test_legacy_task_prompt_field_is_ignored(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("prompts", result)
        self.assertFalse(any("prompt" in key for key in result["token_budget"]))

    def test_heuristic_counts_non_ascii(self) -> None:
        counter = TokenCounter("missing-test-encoding")
        self.assertEqual(counter.count("abcd中文"), 3)

    def test_budget_status(self) -> None:
        status, warnings = budget_status(
            11,
            21,
            {
                "required_warn_tokens": 10,
                "expanded_warn_tokens": 20,
                "hard_max_tokens": None,
            },
        )
        self.assertEqual(status, "WARN")
        self.assertEqual(len(warnings), 2)
        status, _ = budget_status(
            11,
            None,
            {
                "required_warn_tokens": 10,
                "expanded_warn_tokens": 20,
                "hard_max_tokens": 10,
            },
        )
        self.assertEqual(status, "HARD_LIMIT")

    def test_result_is_json_serializable(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        json.dumps(result)

    def test_path_escape_is_blocked(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["../outside.md"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(
            any(
                item["reason"] == "path_escape" and item["severity"] == "ERROR"
                for item in result["context"]["resource_findings"]
            )
        )

    def test_ignored_required_path_is_not_counted(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["src/target.md"]
        data["tasks"]["demo"]["ignore"] = ["src/"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = resolve_task(
            self.root,
            "demo",
            {},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["token_budget"]["required_file_tokens"], 0)
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(
            any(
                item["reason"] == "ignored" and item["severity"] == "ERROR"
                for item in result["context"]["resource_findings"]
            )
        )

    def test_wildcard_directory_ignore(self) -> None:
        (self.root / "archive-old").mkdir()
        (self.root / "archive-old" / "large.md").write_text("ignored", encoding="utf-8")
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["default_rules"]["default_ignore"] = ["archive*/"]
        data["tasks"]["demo"]["required"] = ["archive-old/"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = resolve_task(
            self.root,
            "demo",
            {},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["token_budget"]["required_file_tokens"], 0)

    def test_no_token_count_leaves_zero_measurements(self) -> None:
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=False,
        )
        self.assertFalse(result["token_budget"]["enabled"])
        self.assertEqual(result["token_budget"]["initial_tokens"], 0)

    def test_task_budget_overrides_default(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["budget"] = {"required_warn_tokens": 1}
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["token_budget"]["status"], "WARN")

    def test_missing_required_file_is_an_error(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["src/missing.md"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["token_budget"]["status"], "ERROR")
        self.assertEqual(result["token_budget"]["budget_status"], "PASS")
        self.assertTrue(
            any(
                item["reason"] == "missing"
                and item["resource_class"] == "required"
                and item["severity"] == "ERROR"
                for item in result["context"]["resource_findings"]
            )
        )
        self.assertTrue(any("Missing required resource" in item for item in result["errors"]))

    def test_missing_optional_file_warns_only_when_expanded(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["src/target.md"]
        data["tasks"]["demo"]["optional"] = ["src/missing-optional.md"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["context"]["resource_findings"])

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=True,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["errors"])
        self.assertTrue(
            any(
                item["reason"] == "missing"
                and item["resource_class"] == "optional"
                and item["severity"] == "WARNING"
                for item in result["context"]["resource_findings"]
            )
        )
        self.assertTrue(any("Missing optional resource" in item for item in result["warnings"]))

    def test_optional_placeholder_is_inactive_until_expanded(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["src/target.md"]
        data["tasks"]["demo"]["optional"] = ["<optional-target>/optional.md"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["context"]["unresolved_placeholders"])

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=True,
            count_tokens=True,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["context"]["unresolved_placeholders"],
            ["optional-target"],
        )
        self.assertTrue(
            any("Unresolved optional placeholder" in item for item in result["warnings"])
        )

    def test_cli_returns_nonzero_for_missing_required_file(self) -> None:
        registry_path = self.root / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["tasks"]["demo"]["required"] = ["src/missing.md"]
        registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.workspace.resolve_task_context",
                "demo",
                "--start",
                str(self.root),
                "--format",
                "json",
                "--bind",
                "target=src",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[3],
        )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "ERROR")
        self.assertTrue(payload["errors"])

    def test_missing_preloaded_file_is_an_error(self) -> None:
        (self.root / "AGENTS.md").unlink()

        result = resolve_task(
            self.root,
            "demo",
            {"target": ["src"]},
            include_optional=False,
            count_tokens=True,
        )

        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(
            any(
                item["resource_class"] == "preloaded"
                and item["reason"] == "missing"
                and item["severity"] == "ERROR"
                for item in result["context"]["resource_findings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
