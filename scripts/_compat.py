"""Compatibility support for legacy ``scripts/<name>`` entry points."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import MutableMapping


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def _resolves_to(path_value: str, target: Path) -> bool:
    try:
        return Path(path_value or ".").resolve() == target
    except OSError:
        return False


def ensure_workspace_importable() -> None:
    root = str(WORKSPACE_ROOT)
    script_dir = Path(__file__).resolve().parent
    # Root compatibility adapters execute with ``scripts/`` as sys.path[0].
    # The governed domain package ``scripts/platform`` would otherwise shadow
    # Python's standard-library ``platform`` module in child processes.
    sys.path[:] = [
        entry for entry in sys.path if not _resolves_to(entry, script_dir)
    ]
    if root not in sys.path:
        sys.path.insert(0, root)
    else:
        sys.path.remove(root)
        sys.path.insert(0, root)


def load_legacy_module(
    module_name: str,
    namespace: MutableMapping[str, object],
) -> ModuleType:
    """Load an implementation module and re-export its legacy symbols."""

    ensure_workspace_importable()
    module = importlib.import_module(module_name)
    legacy_name = namespace.get("__name__")
    if isinstance(legacy_name, str) and legacy_name.startswith("scripts."):
        # Make imported legacy modules true aliases, so monkeypatching a
        # historical import path still affects the implementation module.
        sys.modules[legacy_name] = module
    excluded = {"__builtins__", "__cached__", "__loader__", "__name__", "__package__", "__spec__"}
    public_names = []
    for name, value in vars(module).items():
        if name not in excluded:
            namespace[name] = value
            if not name.startswith("_"):
                public_names.append(name)
    namespace["__all__"] = list(getattr(module, "__all__", ())) or public_names
    return module
