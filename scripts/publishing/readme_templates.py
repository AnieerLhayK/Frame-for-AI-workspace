"""Load and render maintainer-editable README templates for projections."""

from __future__ import annotations

from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT


TEMPLATE_ROOT = WORKSPACE_ROOT / "scripts" / "publishing" / "readme_templates"


def load_template(name: str) -> str:
    path = (TEMPLATE_ROOT / name).resolve()
    if TEMPLATE_ROOT.resolve() not in path.parents or not path.is_file():
        raise FileNotFoundError(f"README template is unavailable: {name}")
    return path.read_text(encoding="utf-8")


def render_template(name: str, **values: str) -> str:
    text = load_template(name)
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    unresolved = [part.split("}", 1)[0] for part in text.split("{")[1:] if "}" in part]
    if unresolved:
        raise ValueError(f"README template has unresolved placeholders: {', '.join(unresolved)}")
    return text
