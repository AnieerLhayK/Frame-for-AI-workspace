from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validation import validate_manifest as validator


class ManifestPortabilityTests(unittest.TestCase):
    def test_deployment_roots_explained_but_internal_absolute_still_warns(self):
        state = validator.State()
        validator.check_absolute_paths({
            "runtime_roots": {"mcp": str(Path(tempfile.gettempdir()) / "deployment/mcp")},
            "external_roots": {"research": str(Path(tempfile.gettempdir()) / "deployment/research")},
            "shared": {"source_path": str(Path(tempfile.gettempdir()) / "bad/internal/source")},
        }, state)
        self.assertEqual([f.message for f in state.warnings], [
            "absolute path field may need portability review: shared.source_path"
        ])

    def test_windows_absolute_internal_path_detected_on_every_host(self):
        state = validator.State()
        validator.check_absolute_paths({"shared": {"source_path": "Z:/bad/source"}}, state)
        self.assertEqual(len(state.warnings), 1)

    def test_agent_projection_requires_real_bounded_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "agents"
            target.mkdir()
            (target / "demo.md").write_text("agent", encoding="utf8")
            manifest = {"workspace": {"source_of_truth": str(root)},
                        "shared": {"source_path": "."}, "projections": [{
                            "id": "demo.agent", "kind": "agent", "platform": "demo",
                            "link_path": "agents", "target_path": "agents",
                            "required_files": ["demo.md"],
                        }]}
            with patch.object(validator, "WORKSPACE_ROOT", root):
                state = validator.State()
                validator.check_paths(manifest, state)
                self.assertFalse(any("not referenced" in f.message for f in state.warnings))
                manifest["projections"][0]["required_files"] = ["../outside.md"]
                state = validator.State()
                validator.check_paths(manifest, state)
                self.assertTrue(state.errors)

    def test_unknown_deployment_keys_do_not_hide_internal_absolute_paths(self):
        state = validator.State()
        validator.check_absolute_paths({"runtime_roots": {"mcp": "Z:/installed"}, "packages": [{"source_path": "Z:/source"}]}, state)
        self.assertEqual([item.message for item in state.warnings], ["absolute path field may need portability review: packages[0].source_path"])
