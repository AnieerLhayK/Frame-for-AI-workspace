from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml


from scripts.workspace.runtime import SCRIPTS_ROOT as SCRIPTS_DIR
from scripts.workspace.runtime import WORKSPACE_ROOT

INTENT_ORDER = {
    "behavior": ("skill_source", "shared_policy", "tooling", "registry", "documentation", "memory", "generated_report"),
    "metadata": ("skill_source", "registry", "tooling", "documentation", "memory", "generated_report"),
    "exposure": ("registry", "tooling", "memory", "documentation", "generated_report"),
    "routing": ("routing", "tooling", "documentation", "memory", "generated_report"),
    "tooling": ("tooling", "routing", "documentation", "memory", "generated_report"),
    "policy": ("shared_policy", "registry", "tooling", "documentation", "memory", "generated_report"),
    "documentation": ("documentation", "memory", "routing", "generated_report"),
    "report": ("generated_report", "tooling", "shared_policy", "registry", "documentation", "memory"),
    "migration": ("registry", "tooling", "memory", "documentation", "generated_report"),
    "architecture": ("registry", "shared_policy", "skill_source", "tooling", "documentation", "memory", "generated_report"),
    "general": ("skill_source", "tooling", "registry", "shared_policy", "routing", "documentation", "memory", "generated_report"),
}

PRIMARY_LAYERS = {
    "behavior": {"skill_source"},
    "metadata": {"skill_source", "registry"},
    "exposure": {"registry", "tooling"},
    "routing": {"routing"},
    "tooling": {"tooling"},
    "policy": {"shared_policy", "registry"},
    "documentation": {"documentation"},
    "report": {"generated_report"},
    "migration": {"registry", "tooling"},
    "architecture": {"registry", "shared_policy", "skill_source"},
    "general": {"skill_source", "tooling", "registry", "shared_policy", "routing"},
}


@dataclass
class Candidate:
    path: str
    layer: str
    allowed: bool
    reason: str


@dataclass
class OptionAssessment:
    name: str
    status: str
    score: int
    primary_coverage: bool
    candidates: list[Candidate]
    reasons: list[str]


def normalize_path(value: str) -> str:
    return value.strip().replace("\\", "/").removeprefix("./").rstrip("/")


def is_concrete_scope(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and not any(character.isspace() for character in stripped)


def is_absolute_path(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def load_skill_roots() -> tuple[str, ...]:
    manifest = yaml.safe_load(
        (WORKSPACE_ROOT / "workspace_manifest.yaml").read_text(encoding="utf-8-sig")
    )
    return tuple(
        normalize_path(str(skill["source_path"]))
        for skill in manifest.get("skills", [])
        if skill.get("source_path")
    )


def classify_path(path: str, skill_roots: tuple[str, ...]) -> str:
    normalized = normalize_path(path)
    if is_absolute_path(path):
        return "external_or_projection"
    if normalized == "workspace_manifest.yaml":
        return "registry"
    if normalized in {
        "PROJECT_CONTEXT/tasks/registry/index.yaml",
        "PROJECT_CONTEXT/tasks/registry/index.yaml",
        "USAGE_GUIDES/prompt_registry.yaml",
    }:
        return "routing"
    if normalized == "reports" or normalized.startswith("reports/"):
        return "generated_report"
    if normalized == "scripts" or normalized.startswith("scripts/"):
        return "tooling"
    if normalized == "shared" or normalized.startswith("shared/"):
        return "shared_policy"
    if normalized == "PROJECT_CONTEXT" or normalized.startswith("PROJECT_CONTEXT/"):
        return "memory"
    if (
        normalized == "README.md"
        or normalized in {"USAGE_GUIDES", "WORKSPACE_ENGINEERING", "SKILL_ENGINEERING"}
        or normalized.startswith(
            ("USAGE_GUIDES/", "WORKSPACE_ENGINEERING/", "SKILL_ENGINEERING/")
        )
    ):
        return "documentation"
    if any(normalized == root or normalized.startswith(f"{root}/") for root in skill_roots):
        return "skill_source"
    if normalized.startswith(("skills/", "packages/")):
        return "skill_source"
    if normalized in {"AGENTS.md", ".gitignore"}:
        return "documentation"
    return "workspace_source"


def path_in_scope(path: str, write_scope: list[str]) -> bool:
    normalized = normalize_path(path)
    for scope in write_scope:
        if not is_concrete_scope(scope):
            continue
        allowed = normalize_path(scope)
        if normalized == allowed or normalized.startswith(f"{allowed}/"):
            return True
        scope_path = WORKSPACE_ROOT / allowed
        if scope_path.is_dir() and normalized.startswith(f"{allowed}/"):
            return True
    return False


def parse_option(value: str) -> tuple[str, list[str]]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("option must use NAME=PATH1,PATH2")
    name, raw_paths = value.split("=", 1)
    paths = [item.strip() for item in raw_paths.split(",") if item.strip()]
    if not name.strip() or not paths:
        raise argparse.ArgumentTypeError("option must include a name and at least one path")
    return name.strip(), paths


def resolve_task(task_id: str, bindings: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "resolve_task_context.py"),
        task_id,
        "--format",
        "json",
        "--no-token-count",
    ]
    for binding in bindings:
        command.extend(["--bind", binding])
    result = subprocess.run(
        command,
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(result.stderr.strip() or "task resolver returned invalid JSON") from exc
    if result.returncode != 0 or payload.get("errors"):
        raise RuntimeError("; ".join(payload.get("errors", [])) or "task resolution failed")
    return payload


def automatic_options(
    write_scope: list[str],
    skill_roots: tuple[str, ...],
) -> tuple[list[tuple[str, list[str]]], list[str]]:
    grouped: dict[str, list[str]] = {}
    declarative: list[str] = []
    for path in write_scope:
        if not is_concrete_scope(path):
            declarative.append(path)
            continue
        layer = classify_path(path, skill_roots)
        grouped.setdefault(layer, []).append(path)
    return [(layer.replace("_", "-"), paths) for layer, paths in grouped.items()], declarative


def assess_option(
    name: str,
    paths: list[str],
    intent: str,
    write_scope: list[str],
    skill_roots: tuple[str, ...],
) -> OptionAssessment:
    order = INTENT_ORDER[intent]
    layer_scores = {layer: 100 - (index * 12) for index, layer in enumerate(order)}
    candidates: list[Candidate] = []
    reasons: list[str] = []

    for path in paths:
        layer = classify_path(path, skill_roots)
        allowed = path_in_scope(path, write_scope)
        reason = "inside resolved write scope" if allowed else "outside resolved write scope"
        if layer == "external_or_projection":
            allowed = False
            reason = "absolute or platform-facing paths are not source edit targets"
        candidates.append(Candidate(path, layer, allowed, reason))

    invalid = [candidate for candidate in candidates if not candidate.allowed]
    layers = {candidate.layer for candidate in candidates if candidate.allowed}
    primary_coverage = bool(layers & PRIMARY_LAYERS[intent])
    score = max((layer_scores.get(layer, 35) for layer in layers), default=0)
    score -= max(0, len(candidates) - 1) * 3

    if invalid:
        reasons.append("option contains paths outside the task's resolved authority")
        return OptionAssessment(name, "BLOCKED", -100, False, candidates, reasons)
    if layers == {"generated_report"} and intent != "report":
        reasons.append("generated snapshots cannot be the sole source change for this intent")
        return OptionAssessment(name, "BLOCKED", -80, False, candidates, reasons)
    if not primary_coverage:
        score -= 30
        reasons.append("option covers supporting layers only; inspect the owning source layer first")
        status = "SUPPORTING_ONLY"
    else:
        reasons.append("option includes an owning layer for the declared intent")
        status = "VIABLE"
    if len(candidates) > 1:
        reasons.append("score includes a small breadth penalty; retain only evidence-required files")
    return OptionAssessment(name, status, score, primary_coverage, candidates, reasons)


def build_plan(
    task_id: str,
    intent: str,
    goal: str | None,
    bindings: list[str],
    raw_options: list[str],
) -> dict[str, Any]:
    task = resolve_task(task_id, bindings)
    write_scope = list(task["context"]["write_scope"])
    skill_roots = load_skill_roots()
    declarative: list[str] = []
    if raw_options:
        options = [parse_option(value) for value in raw_options]
    else:
        options, declarative = automatic_options(write_scope, skill_roots)

    assessments = [
        assess_option(name, paths, intent, write_scope, skill_roots)
        for name, paths in options
    ]
    assessments.sort(key=lambda option: option.score, reverse=True)
    viable = [option for option in assessments if option.status == "VIABLE"]
    recommendation = viable[0].name if viable else None
    return {
        "status": "PASS" if recommendation else "NEEDS_REVIEW",
        "task": task["task"],
        "intent": intent,
        "goal": goal,
        "write_scope": write_scope,
        "declarative_scopes": declarative,
        "recommendation": recommendation,
        "options": [asdict(option) for option in assessments],
        "guardrails": [
            "Treat the recommendation as a starting layer, not permission to edit every listed path.",
            "Read the nearest owning source before expanding to supporting documentation or snapshots.",
            "Never edit platform projections or generated reports as substitutes for source changes.",
            "If two viable options remain close, inspect call sites and validation impact before choosing.",
        ],
    }


def render_text(plan: dict[str, Any]) -> None:
    print(f"Task: {plan['task']['id']}")
    print(f"Intent: {plan['intent']}")
    if plan["goal"]:
        print(f"Goal: {plan['goal']}")
    print(f"Status: {plan['status']}")
    print(f"Recommendation: {plan['recommendation'] or 'manual review required'}")
    for option in plan["options"]:
        print(f"\n{option['name']}: {option['status']} (score {option['score']})")
        for candidate in option["candidates"]:
            print(
                f"  - {candidate['path']} [{candidate['layer']}] "
                f"{'allowed' if candidate['allowed'] else 'blocked'}"
            )
        for reason in option["reasons"]:
            print(f"  reason: {reason}")
    if plan["declarative_scopes"]:
        print("\nDeclarative scopes requiring explicit resolution:")
        for scope in plan["declarative_scopes"]:
            print(f"  - {scope}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank candidate change surfaces without modifying files."
    )
    parser.add_argument("task_id")
    parser.add_argument("--intent", choices=tuple(INTENT_ORDER), required=True)
    parser.add_argument("--goal")
    parser.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="NAME=PATH1,PATH2",
        help="Compare explicit candidate file sets. Repeat for alternatives.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        plan = build_plan(args.task_id, args.intent, args.goal, args.bind, args.option)
    except (RuntimeError, argparse.ArgumentTypeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, indent=2))
        return 1

    if args.format == "json":
        print(json.dumps(plan, indent=2))
    else:
        render_text(plan)
    return 0 if plan["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
