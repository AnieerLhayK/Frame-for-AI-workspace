from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
TRACKED_TOGGLE_RELATIVE = Path(".claude") / "model-routing-advice.json"
LOCAL_TOGGLE_RELATIVE = Path(".claude") / "model-routing-advice.local.json"
TOGGLE_RELATIVE = TRACKED_TOGGLE_RELATIVE
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


def load_toggle_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return None, "toggle file is missing"
    except (OSError, ValueError) as exc:
        return None, str(exc)


def load_toggle(project_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    local_path = project_root / LOCAL_TOGGLE_RELATIVE
    local_toggle, local_error = load_toggle_file(local_path)
    if isinstance(local_toggle, dict):
        return local_toggle, None
    tracked_path = project_root / TRACKED_TOGGLE_RELATIVE
    tracked_toggle, tracked_error = load_toggle_file(tracked_path)
    if isinstance(tracked_toggle, dict):
        return tracked_toggle, tracked_error
    return None, local_error if local_path.exists() else tracked_error


def effective_toggle(project_root: Path) -> dict[str, Any]:
    local_path = project_root / LOCAL_TOGGLE_RELATIVE
    tracked_path = project_root / TRACKED_TOGGLE_RELATIVE
    local_toggle, local_error = load_toggle_file(local_path)
    tracked_toggle, tracked_error = load_toggle_file(tracked_path)
    if isinstance(local_toggle, dict):
        return {
            "payload": local_toggle,
            "error": local_error,
            "source": "local override",
            "path": local_path,
            "local_payload": local_toggle,
            "tracked_payload": tracked_toggle,
            "local_error": local_error,
            "tracked_error": tracked_error,
        }
    return {
        "payload": tracked_toggle,
        "error": tracked_error,
        "source": "tracked default",
        "path": tracked_path,
        "local_payload": local_toggle,
        "tracked_payload": tracked_toggle,
        "local_error": local_error,
        "tracked_error": tracked_error,
    }


def write_toggle(project_root: Path, enabled: bool, *, scope: str = "local") -> None:
    relative = LOCAL_TOGGLE_RELATIVE if scope == "local" else TRACKED_TOGGLE_RELATIVE
    path = project_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    payload, _ = load_toggle_file(path)
    if not isinstance(payload, dict):
        payload = default_toggle()
    payload["interface_version"] = int(payload.get("interface_version") or 1)
    payload["enabled"] = enabled
    payload.setdefault("mode", "advisory_pause")
    payload.setdefault("description", default_toggle()["description"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_status(project_root: Path) -> dict[str, Any]:
    effective = effective_toggle(project_root)
    toggle = effective["payload"]
    toggle_error = effective["error"]
    local_toggle = effective["local_payload"]
    tracked_toggle = effective["tracked_payload"]
    hook_text = read_text(project_root / HOOK_RELATIVE)
    settings_text = read_text(project_root / SETTINGS_RELATIVE)
    claude_text = read_text(project_root / CLAUDE_RELATIVE)
    policy_text = read_text(project_root / POLICY_RELATIVE)
    global_claude_text = read_text(Path.home() / ".claude" / "CLAUDE.md")
    global_rules_text = read_text(Path.home() / ".claude" / "global_rules.md")
    enabled = toggle.get("enabled") if isinstance(toggle, dict) else None
    hook_honors_toggle = (
        "Test-ModelAdviceEnabled" in hook_text
        and "model-routing-advice.local.json" in hook_text
        and "model-routing-advice.json" in hook_text
    )
    settings_mentions_hook = "model_routing_guard.ps1" in settings_text
    claude_mentions_toggle = ".claude/model-routing-advice.json" in claude_text
    claude_imports_policy = "@shared/claude/policies/model-routing-policy.md" in claude_text
    claude_static_markers = any(
        marker in claude_text
        for marker in (
            "Flash sufficient",
            "Recommend Pro",
            "deepseek-v4-pro",
        )
    )
    static_prompt_layer_clean = not claude_imports_policy and not claude_static_markers
    policy_mentions_toggle = ".claude/model-routing-advice.json" in policy_text
    integration_installed = (
        isinstance(enabled, bool)
        and hook_honors_toggle
        and settings_mentions_hook
        and claude_mentions_toggle
        and policy_mentions_toggle
    )
    runtime_enforcement = (
        "enabled"
        if enabled is True and integration_installed
        else "disabled"
        if enabled is False and integration_installed
        else "unavailable"
    )
    disabled_is_clean = enabled is False and (
        hook_honors_toggle or not settings_mentions_hook
    ) and static_prompt_layer_clean
    prompt_layer = (
        "enabled by hook injection"
        if enabled is True and hook_honors_toggle and settings_mentions_hook
        else "disabled"
        if enabled is False and static_prompt_layer_clean
        else "leaking static instructions"
        if enabled is False
        else "unavailable"
    )
    global_tiering_present = "deepseek-v4-pro" in global_claude_text or "deepseek-v4-pro" in global_rules_text
    global_disable_compatible = (
        "Project-level instructions may override, extend, or disable this behavior" in global_claude_text
        or "project-level model advice toggle is disabled" in global_rules_text
        or "项目级" in global_rules_text and "关闭" in global_rules_text
    )
    fully_disabled = (
        enabled is False
        and runtime_enforcement == "disabled"
        and prompt_layer == "disabled"
        and (not global_tiering_present or global_disable_compatible)
    )
    return {
        "project_root": str(project_root),
        "toggle_path": str(effective["path"]),
        "toggle_source": effective["source"],
        "tracked_toggle_path": str(project_root / TRACKED_TOGGLE_RELATIVE),
        "local_toggle_path": str(project_root / LOCAL_TOGGLE_RELATIVE),
        "enabled": enabled,
        "tracked_enabled": (
            tracked_toggle.get("enabled") if isinstance(tracked_toggle, dict) else None
        ),
        "local_enabled": local_toggle.get("enabled") if isinstance(local_toggle, dict) else None,
        "toggle_error": toggle_error,
        "toggle_file": Path(effective["path"]).exists(),
        "tracked_toggle_file": (project_root / TRACKED_TOGGLE_RELATIVE).exists(),
        "local_toggle_file": (project_root / LOCAL_TOGGLE_RELATIVE).exists(),
        "hook_file": (project_root / HOOK_RELATIVE).exists(),
        "hook_honors_toggle": hook_honors_toggle,
        "settings_mentions_hook": settings_mentions_hook,
        "claude_mentions_toggle": claude_mentions_toggle,
        "claude_imports_policy": claude_imports_policy,
        "claude_static_markers": claude_static_markers,
        "static_prompt_layer_clean": static_prompt_layer_clean,
        "policy_mentions_toggle": policy_mentions_toggle,
        "integration_installed": integration_installed,
        "runtime_enforcement": runtime_enforcement,
        "prompt_layer": prompt_layer,
        "global_tiering_present": global_tiering_present,
        "global_disable_compatible": global_disable_compatible,
        "fully_disabled": fully_disabled,
        "will_inject_or_block": runtime_enforcement == "enabled",
        "disabled_is_clean": disabled_is_clean,
        "external_interface": {
            "contract": str(TRACKED_TOGGLE_RELATIVE).replace("\\", "/"),
            "local_override": str(LOCAL_TOGGLE_RELATIVE).replace("\\", "/"),
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
    print(
        "Runtime enforcement: "
        f"{status['runtime_enforcement']} "
        f"({'will inject/pause' if status['will_inject_or_block'] else 'will not inject or block'})"
    )
    print(f"Project: {status['project_root']}")
    print(f"Toggle: {status['toggle_path']}")
    print(f"Source: {status['toggle_source']}")
    print(f"Tracked default: {format_enabled(status['tracked_enabled'])}")
    print(f"Local override: {format_enabled(status['local_enabled'])}")
    if status["toggle_error"]:
        print(f"Toggle issue: {status['toggle_error']}")
    print("Effective layers:")
    print(f"  - hook injection/enforcement: {status['runtime_enforcement']}")
    print(f"  - static CLAUDE.md prompt layer: {status['prompt_layer']}")
    print(
        "  - global tiering rule: "
        f"{'compatible' if status['global_disable_compatible'] else 'present; review recommended' if status['global_tiering_present'] else 'not detected'}"
    )
    print("Integration:")
    print(f"  - toggle file: {'present' if status['toggle_file'] else 'missing'}")
    print(f"  - hook file: {'present' if status['hook_file'] else 'missing'}")
    print(f"  - hook honors toggle: {'yes' if status['hook_honors_toggle'] else 'no'}")
    print(f"  - settings uses hook: {'yes' if status['settings_mentions_hook'] else 'no'}")
    print(f"  - CLAUDE.md documents toggle: {'yes' if status['claude_mentions_toggle'] else 'no'}")
    print(f"  - CLAUDE.md avoids static routing template: {'yes' if status['static_prompt_layer_clean'] else 'no'}")
    print(f"  - shared policy documents toggle: {'yes' if status['policy_mentions_toggle'] else 'no'}")
    print(f"Installed: {'yes' if status['integration_installed'] else 'no'}")
    if status["enabled"] is False:
        print(f"Disabled behavior clean: {'yes' if status['disabled_is_clean'] else 'needs review'}")
        print(f"Fully off: {'yes' if status['fully_disabled'] else 'no'}")
    if not status["integration_installed"]:
        print(
            "Note: external projects need the toggle file plus Claude hook/settings "
            "and a lightweight CLAUDE.md toggle rule before this switch can affect "
            "Claude Code behavior."
        )


def format_enabled(value: object) -> str:
    if value is True:
        return "ON"
    if value is False:
        return "OFF"
    return "not set"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or toggle Claude model advice integration.")
    parser.add_argument("action", choices=("status", "on", "off"))
    parser.add_argument("--project-root", default=str(WORKSPACE_ROOT))
    parser.add_argument(
        "--scope",
        choices=("local", "tracked"),
        default="local",
        help="For on/off, write the ignored local override by default; use tracked to change the project default.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(f"Project root does not exist or is not a directory: {project_root}", file=sys.stderr)
        return 2
    if args.action in {"on", "off"}:
        write_toggle(project_root, enabled=args.action == "on", scope=args.scope)
    status = project_status(project_root)
    if args.format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        render_text(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
