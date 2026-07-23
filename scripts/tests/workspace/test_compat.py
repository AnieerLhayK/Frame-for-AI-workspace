from __future__ import annotations

import sys
import unittest
from pathlib import Path

from scripts import _compat


class CompatibilityTests(unittest.TestCase):
    def test_adapter_removes_script_directory_from_import_path(self) -> None:
        script_dir = Path(_compat.__file__).resolve().parent
        original = list(sys.path)
        try:
            sys.path.insert(0, str(script_dir))
            _compat.ensure_workspace_importable()
            self.assertNotIn(str(script_dir), sys.path)
            self.assertEqual(sys.path[0], str(_compat.WORKSPACE_ROOT))
        finally:
            sys.path[:] = original


if __name__ == "__main__":
    unittest.main()
