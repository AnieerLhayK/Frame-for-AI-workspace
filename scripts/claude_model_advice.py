from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
TOGGLE_RELATIVE = Path(".claude") / "model-routing-advice.json"
HOOK_RELATIVE = Path(".claude") / "hooks" / "model_routing_guard.ps1"
SETTINGS_RELATIVE = Path(".claude") / "settings.json"
CLAUDE_RELATIVE = Path("CLAUDE.md")
POLICY_RELATIVE = Path("shared") / "claude" / "policies" / "model-routing-policy.md"


def default_toggle() -> dict[str, Any]:
    return {
        "interface_version": 1,
        "enabled": True,
        "mode": "advisory_pause",
        "description": (
            "Developer-facing switch for Claude model-tier advice. Set enabled "
            "to false to disable advice injection and pre-tool enforcement "
            "without changing model configuration or permissions."
        ),
    }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError:
        return ""


def load_toggle(project_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    path = project_root / TOGGLE_RELATIVE
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return None, "toggle file is missing"
    except (OSError, ValueError) as exc:
        return None, str(exc)


def write_toggle(project_root: Path, enabled: bool) -> None:
    path = project_root / TOGGLE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload, _ = load_toggle(project_root)
    if not isinstance(payload, dict):
        payload = default_toggle()
    payload["interface_version"] = int(payload.get("interface_version") or 1)
    payload["enabled"] = enabled
    payload.setdefault("mode", "advisory_pause")
    payload.setdefault("description", default_toggle()["description"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_status(project_root: Path) -> dict[str, Any]:
    toggle, toggle_error = load_toggle(project_root)
    hook_text = read_text(project_root / HOOK_RELATIVE)
    settings_text = read_text(project_root / SETTINGS_RELATIVE)
    claude_text = read_text(project_root / CLAUDE_RELATIVE)
    policy_text = read_text(project_root / POLICY_RELATIVE)
    enabled = toggle.get("enabled") if isinstance(toggle, dict) else None
    hook_honors_toggle = (
        "Test-ModelAdviceEnabled" in hook_text
        and ".claude\\model-routing-advice.json" in hook_text
    )
    settings_mentions_hook = "model_routing_guard.ps1" in settings_text
    claude_mentions_toggle = ".claude/model-routing-advice.json" in claude_text
    policy_mentions_toggle = ".claude/model-routing-advice.json" in policy_text
    integration_installed = (
        isinstance(enabled, bool)
        and hook_honors_toggle
        and settings_mentions_hook
        and claude_mentions_toggle
        and policy_mentions_toggle
    )
    disabled_is_clean = enabled is False and (
        hook_honors_toggle or not settings_mentions_hook
    )
    return {
        "project_root": str(project_root),
        "toggle_path": str(project_root / TOGGLE_RELATIVE),
        "enabled": enabled,
        "toggle_error": toggle_error,
        "toggle_file": (project_root / TOGGLE_RELATIVE).exists(),
        "hook_file": (project_root / HOOK_RELATIVE).exists(),
        "hook_honors_toggle": hook_honors_toggle,
        "settings_mentions_hook": settings_mentions_hook,
        "claude_mentions_toggle": claude_mentions_toggle,
        "policy_mentions_toggle": policy_mentions_toggle,
        "integration_installed": integration_installed,
        "disabled_is_clean": disabled_is_clean,
        "external_interface": {
            "contract": str(TOGGLE_RELATIVE).replace("\\", "/"),
            "commands": [
                "workspace claude model-advice status --project-root <git-root>",
                "workspace claude model-advice on --project-root <git-root>",
                "workspace claude model-advice off --project-root <git-root>",
            ],
        },
    }


def render_text(status: dict[str, Any]) -> None:
    state = "ON" if status["enabled"] is True else "OFF" if status["enabled"] is False else "UNKNOWN"
    print(f"Claude model advice: {state}")
    print(f"Project: {status['project_root']}")
    print(f"Toggle: {status['toggle_path']}")
    if status["toggle_error"]:
        print(f"Toggle issue: {status['toggle_error']}")
    print("Integration:")
    print(f"  - toggle file: {'present' if status['toggle_file'] else 'missing'}")
    print(f"  - hook file: {'present' if status['hook_file'] else 'missing'}")
    print(f"  - hook honors toggle: {'yes' if status['hook_honors_toggle'] else 'no'}")
    print(f"  - settings uses hook: {'yes' if status['settings_mentions_hook'] else 'no'}")
    print(f"  - CLAUDE.md documents toggle: {'yes' if status['claude_mentions_toggle'] else 'no'}")
    print(f"  - shared policy documents toggle: {'yes' if status['policy_mentions_toggle'] else 'no'}")
    print(f"Ready: {'yes' if status['integration_installed'] else 'no'}")
    if status["enabled"] is False:
        print(f"Disabled behavior clean: {'yes' if status['disabled_is_clean'] else 'needs review'}")
    if not status["integration_installed"]:
        print(
            "Note: external projects need the toggle file plus Claude hook/settings "
            "and policy references before this switch can affect Claude Code behavior."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or toggle Claude model advice integration.")
    parser.add_argument("action", choices=("status", "on", "off"))
    parser.add_argument("--project-root", default=str(WORKSPACE_ROOT))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(f"Project root does not exist or is not a directory: {project_root}", file=sys.stderr)
        return 2
    if args.action in {"on", "off"}:
        write_toggle(project_root, enabled=args.action == "on")
    status = project_status(project_root)
    if args.format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        render_text(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
