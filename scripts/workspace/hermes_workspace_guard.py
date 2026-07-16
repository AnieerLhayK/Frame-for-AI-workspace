from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from scripts.workspace.agent_governance import (
        POLICY_PATH,
        check_access,
        classify_path,
        is_absolute_path,
        load_manifest,
        load_registry,
        load_yaml,
    )


from scripts.workspace.runtime import WORKSPACE_ROOT
HERMES_HOME = Path(
    os.environ.get("HERMES_HOME", r"${DATA_ROOT}/hermes")
).resolve()
HERMES_SKILLS_ROOT = HERMES_HOME / "skills"
CHARACTER_RUNTIME_RECORD_ROOT = (
    WORKSPACE_ROOT
    / "packages"
    / "character-system"
    / "reports"
    / "runtime-loop"
)
STATE_ROOT = Path(
    os.environ.get(
        "WORKSPACE_GOVERNANCE_RUNTIME",
        r"${DATA_ROOT}/workspace-governance\runtime\hermes",
    )
)

DIRECT_WRITE_TOOLS = {"write_file", "patch"}
ALWAYS_BLOCKED_TOOLS = {"skill_manage", "execute_code", "process"}
MCP_MUTATION_MARKERS = (
    "write",
    "edit",
    "patch",
    "create",
    "move",
    "rename",
    "delete",
    "remove",
    "save",
    "upload",
)
PATH_KEYS = {
    "path",
    "paths",
    "filepath",
    "filepaths",
    "file_path",
    "source",
    "destination",
    "target",
    "directory",
    "root",
    "output_path",
    "input_path",
    "old_path",
    "new_path",
}
READ_ONLY_MCP_ACTIONS = {
    "activate",
    "cache_status",
    "close",
    "compare",
    "count",
    "cross_references",
    "doc_properties",
    "document_structure",
    "errors",
    "find",
    "find_all",
    "find_format",
    "find_text",
    "format_diff",
    "full_structure",
    "full_text",
    "get",
    "health_check",
    "info",
    "list",
    "list_all",
    "operation_status",
    "outline",
    "page_dimensions",
    "paragraph",
    "paragraphs",
    "range",
    "read",
    "recent",
    "runs_detail",
    "section_info",
    "selection",
    "semantic_structure",
    "stats",
    "summary",
    "table_dimensions",
    "text_diff",
}
READ_ONLY_MCP_ACTION_PREFIXES = (
    "get_",
    "list_",
    "read_",
    "find_",
    "query_",
    "inspect_",
    "analyze_",
)
READ_ONLY_TERMINAL_PATTERNS = (
    r"^\s*git\s+(status|diff|log|show|branch(\s+--show-current)?|rev-parse)\b",
    r"^\s*(rg|where|where\.exe|type|dir|ls)\b",
    r"^\s*(get-content|get-childitem|get-item|select-string|test-path)\b",
    r"^\s*python\s+scripts[\\/](workspace_cli|agent_governance)\.py\s+"
    r"(agent\s+(status|list|show|validate|doctor|check)|health|summary|"
    r"reports\s+status|knowledge\s+(find|list|validate)|changes\s+(plan|verify)|"
    r"workflow\s+check)\b",
)
REQUEST_COMMAND_PATTERN = re.compile(
    r"^\s*python\s+scripts[\\/](workspace_cli|agent_governance)\.py\s+"
    r"agent\s+request\b",
    re.IGNORECASE,
)
UNSAFE_TERMINAL_COMPOSITION = re.compile(r"[;&|><`\r\n]|\$\(")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_path(value: str, cwd: str | None) -> str:
    expanded = os.path.expandvars(os.path.expanduser(value.strip().strip("\"'")))
    if is_absolute_path(expanded):
        return expanded
    base = str(cwd or WORKSPACE_ROOT)
    if PureWindowsPath(base).is_absolute():
        return str(PureWindowsPath(base) / PureWindowsPath(expanded))
    if PurePosixPath(base).is_absolute():
        return str(PurePosixPath(base) / PurePosixPath(expanded))
    return str((WORKSPACE_ROOT / Path(base) / Path(expanded)).resolve(strict=False))


def _session_state_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")
    return STATE_ROOT / f"{safe}.json"


def _read_active_skill(session_id: str) -> str | None:
    try:
        payload = json.loads(
            _session_state_path(session_id).read_text(encoding="utf-8")
        )
    except (OSError, ValueError, TypeError):
        return None
    value = payload.get("active_skill")
    return str(value) if value else None


def _record_active_skill(session_id: str, tool_input: dict[str, Any]) -> None:
    skill = tool_input.get("name")
    if not isinstance(skill, str) or not skill.strip():
        return
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    target = _session_state_path(session_id)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"active_skill": skill.strip()}, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(target)


def _collect_path_values(value: Any, key: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            paths.extend(_collect_path_values(child_value, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            paths.extend(_collect_path_values(child, key))
    elif isinstance(value, str) and key.casefold() in PATH_KEYS:
        paths.append(value)
    return paths


def _patch_paths(tool_input: dict[str, Any]) -> list[str]:
    paths = _collect_path_values(tool_input)
    patch = tool_input.get("patch")
    if isinstance(patch, str):
        paths.extend(
            match.group(1).strip()
            for match in re.finditer(
                r"^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s*(.+)$",
                patch,
                re.MULTILINE,
            )
        )
    return paths


def _terminal_is_read_only(command: str) -> bool:
    if UNSAFE_TERMINAL_COMPOSITION.search(command):
        return False
    return any(
        re.search(pattern, command, re.IGNORECASE)
        for pattern in READ_ONLY_TERMINAL_PATTERNS
    )


def _terminal_is_agent_request(command: str) -> bool:
    return (
        not UNSAFE_TERMINAL_COMPOSITION.search(command)
        and bool(REQUEST_COMMAND_PATTERN.search(command))
    )


def _mcp_is_mutating(tool_name: str, tool_input: dict[str, Any]) -> bool:
    action = str(tool_input.get("action") or "").strip().casefold()
    if action:
        return not (
            action in READ_ONLY_MCP_ACTIONS
            or action.startswith(READ_ONLY_MCP_ACTION_PREFIXES)
        )
    return any(
        marker in tool_name.casefold() for marker in MCP_MUTATION_MARKERS
    )


def _skill_is_workspace_skill(skill: str | None) -> bool:
    if not skill:
        return False
    manifest = load_manifest()
    return any(
        str(item.get("id", "")).casefold() == skill.casefold()
        for item in manifest.get("skills", [])
    )


def _path_is_workspace_context(value: str, cwd: str | None = None) -> bool:
    policy = load_yaml(POLICY_PATH)
    manifest = load_manifest()
    target = classify_path(policy, manifest, _resolve_path(value, cwd))
    return target["surface"] != "external_environment"


def _command_mentions_workspace(command: str) -> bool:
    normalized = command.replace("/", "\\").casefold()
    manifest = load_manifest()
    source_root = manifest.get("workspace", {}).get("source_of_truth")
    roots = [
        str(WORKSPACE_ROOT),
        str(source_root or ""),
        str(HERMES_SKILLS_ROOT),
        *(
            str(value)
            for value in manifest.get("platform_roots", {}).values()
        ),
    ]
    return any(
        root
        and root.replace("/", "\\").rstrip("\\").casefold() in normalized
        for root in roots
    )


def _workspace_context(
    *,
    active_skill: str | None,
    cwd: str | None,
    command: str = "",
) -> bool:
    return (
        _skill_is_workspace_skill(active_skill)
        or _path_is_workspace_context(str(cwd or WORKSPACE_ROOT))
        or _command_mentions_workspace(command)
    )


def _block(message: str) -> dict[str, str]:
    return {"action": "block", "message": message}


def _authorization_message(result: dict[str, Any], active_skill: str | None) -> str:
    skill_note = f" Acting skill: {active_skill}." if active_skill else ""
    return (
        "Workspace governance blocked this Hermes tool call. "
        f"{result.get('reason', 'write is outside effective authority')}."
        f"{skill_note} Hermes is a record_producer: use style-doctor and write "
        "a diagnosis/handoff under the allowed runtime-loop record paths, or "
        "create reports/agent-requests for Codex/Claude review. Do not patch "
        "skill source, governance files, or platform projections."
    )


def _check_paths(
    values: list[str],
    *,
    cwd: str | None,
    active_skill: str | None,
) -> dict[str, str] | None:
    policy = load_yaml(POLICY_PATH)
    manifest = load_manifest()
    registry = load_registry()
    checked = False
    for value in values:
        path = _resolve_path(value, cwd)
        target = classify_path(policy, manifest, path)
        if target["surface"] == "external_environment":
            continue
        checked = True
        if target["surface"] == "runtime_record" and not active_skill:
            return _block(
                "Workspace governance requires an active record-writing Skill "
                "for character runtime-loop records. Load style-doctor for "
                "diagnosis or handoff work; runtime character Skills cannot "
                "write these records."
            )
        result = check_access(
            policy,
            manifest,
            agent_name="hermes",
            operation="write",
            raw_path=path,
            acting_skill=active_skill,
            registry=registry,
        )
        if result["status"] != "ALLOW":
            return _block(_authorization_message(result, active_skill))
    if not checked and values:
        return None
    return None


def evaluate(payload: dict[str, Any]) -> dict[str, str]:
    event = str(payload.get("hook_event_name") or "")
    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    session_id = str(payload.get("session_id") or "")
    cwd = str(payload.get("cwd") or WORKSPACE_ROOT)

    if event == "post_tool_call" and tool_name == "skill_view":
        _record_active_skill(session_id, tool_input)
        return {}

    active_skill = _read_active_skill(session_id)
    if event == "pre_llm_call":
        if not _workspace_context(active_skill=active_skill, cwd=cwd):
            return {}
        skill_note = f" Active skill: {active_skill}." if active_skill else ""
        return {
            "context": (
                "[Workspace authority] Hermes is a record_producer. It may "
                "read/invoke skills and write only scoped diagnosis, handoff, "
                "Hermes report, or agent-request records. It must never patch "
                "skill source, governance, or projections. A user request does "
                "not expand authority: never offer, suggest, ask permission for, "
                "or attempt a direct source patch. Character drift routes "
                "immediately through style-doctor -> diagnosis/handoff -> "
                "character-maintainer. Shared runtime-loop policy, templates, "
                "and existing records are available through the read-only "
                "filesystem MCP at their canonical package paths. Tool "
                "enforcement is active."
                + skill_note
            )
        }

    if event != "pre_tool_call":
        return {}

    in_workspace_context = _workspace_context(
        active_skill=active_skill,
        cwd=str(tool_input.get("cwd") or cwd),
    )

    if tool_name in ALWAYS_BLOCKED_TOOLS and in_workspace_context:
        return _block(
            f"Workspace governance blocks Hermes tool '{tool_name}'. "
            "Use a change request or an approved isolated lease."
        )

    if tool_name == "terminal":
        command = str(tool_input.get("command") or "")
        in_workspace_context = _workspace_context(
            active_skill=active_skill,
            cwd=str(tool_input.get("cwd") or cwd),
            command=command,
        )
        if not in_workspace_context:
            return {}
        if _terminal_is_agent_request(command) or _terminal_is_read_only(command):
            return {}
        return _block(
            "Workspace governance blocks mutating or unclassified terminal "
            "commands from Hermes. Use read-only inspection, write an allowed "
            "diagnosis/handoff with path-checked file tools, or create an "
            "agent change request."
        )

    mutating_mcp = tool_name.startswith("mcp_") and _mcp_is_mutating(
        tool_name,
        tool_input,
    )
    if tool_name in DIRECT_WRITE_TOOLS or mutating_mcp:
        paths = _patch_paths(tool_input)
        if not paths:
            return _block(
                f"Workspace governance could not resolve a target path for "
                f"mutating tool '{tool_name}', so the call failed closed."
            )
        return _check_paths(
            paths,
            cwd=str(tool_input.get("cwd") or cwd),
            active_skill=active_skill,
        ) or {}

    return {}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        result = _block(
            "Workspace governance guard failed closed before a Hermes tool "
            f"call: {type(exc).__name__}: {exc}"
        )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
