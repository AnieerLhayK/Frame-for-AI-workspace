from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


from scripts.workspace.runtime import WORKSPACE_ROOT
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
SKILL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PORTABILITY_VALUES = {"portable", "host-adapted", "workspace-bound"}
DISTRIBUTION_VALUES = {"internal-only", "review-required", "redistributable"}
RUNTIME_SCAN_DIRECTORIES = ("scripts", "config", "agents")
RUNTIME_SCAN_SUFFIXES = {".py", ".ps1", ".sh", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
HOST_REQUIREMENTS = {"windows", "windows-powershell", "workspace-cli", "optional-workspace-manifest"}
HOST_REQUIREMENT_PREFIXES = ("host-",)


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("workspace manifest must be an object")
    return payload


def workspace_root(manifest: dict[str, Any]) -> Path:
    value = manifest.get("workspace", {}).get("source_of_truth")
    if not value:
        raise ValueError("manifest workspace.source_of_truth is missing")
    return Path(str(value)).resolve()


def resolve_workspace_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path must stay inside workspace source root: {value}") from exc
    return resolved


def manifest_skill(manifest: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    return next(
        (
            skill
            for skill in manifest.get("skills", [])
            if isinstance(skill, dict) and str(skill.get("id")) == skill_id
        ),
        None,
    )


def manifest_skill_by_source(
    manifest: dict[str, Any],
    source_path: str,
) -> dict[str, Any] | None:
    normalized = source_path.replace("\\", "/").strip("/")
    return next(
        (
            skill
            for skill in manifest.get("skills", [])
            if isinstance(skill, dict)
            and str(skill.get("source_path", "")).replace("\\", "/").strip("/")
            == normalized
        ),
        None,
    )


def source_path_requires_contract(source_path: str) -> bool:
    """Standalone source packages live under the manifest's skills/ root."""
    normalized = source_path.replace("\\", "/").strip("/")
    return normalized.startswith("skills/")


def projection_by_id(manifest: dict[str, Any], projection_id: str) -> dict[str, Any] | None:
    return next(
        (
            projection
            for projection in manifest.get("projections", [])
            if isinstance(projection, dict) and str(projection.get("id")) == projection_id
        ),
        None,
    )


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return None, str(exc)
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return None, "SKILL.md must start with YAML frontmatter"
    try:
        payload = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(payload, dict):
        return None, "YAML frontmatter must be a mapping"
    return payload, None


def runtime_contract_files(source: Path) -> list[Path]:
    """Return executable/configuration surfaces, excluding documentation examples."""
    files = [source / "SKILL.md"]
    for directory_name in RUNTIME_SCAN_DIRECTORIES:
        directory = source / directory_name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            relative = path.relative_to(source)
            if not path.is_file() or "__pycache__" in relative.parts:
                continue
            if path.suffix.lower() in RUNTIME_SCAN_SUFFIXES:
                files.append(path)
    return files


def assignment_strings(path: Path) -> list[str]:
    """Extract literal Python assignment values, not detector expressions or prose."""
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    values: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [target.id.lower() for target in targets if isinstance(target, ast.Name)]
        if any(name.endswith(("_markers", "_patterns")) for name in names):
            continue
        if node.value is None:
            continue
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and isinstance(child.func.value, ast.Name)
            and child.func.value.id == "re"
            and child.func.attr == "compile"
            for child in ast.walk(node.value)
        ):
            continue
        for child in ast.walk(node.value):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                values.append(child.value)
    return values


def normalized_host_couplings(source: Path) -> set[str]:
    """Find host-bound runtime references without treating reference material as code."""
    couplings: set[str] = set()
    for path in runtime_contract_files(source):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        values = assignment_strings(path) if path.suffix.lower() == ".py" else [text]
        normalized_values = [
            re.sub(r"/+", "/", value.replace("\\", "/").lower()) for value in values
        ]
        if any(re.search(r"\b[a-z]:/", value) for value in normalized_values):
            couplings.add("windows-path")
        if any("workspace_manifest.yaml" in value for value in normalized_values):
            couplings.add("workspace-manifest")
        if any(
            re.search(r"(?:^|[^a-z0-9_-])workspace(?:\.cmd)?\s+(?:records|task|agent|skill)\b", value)
            for value in normalized_values
        ):
            couplings.add("workspace-cli")
    return couplings


def has_host_requirement(requires: list[str]) -> bool:
    return any(
        requirement in HOST_REQUIREMENTS
        or requirement.startswith(HOST_REQUIREMENT_PREFIXES)
        for requirement in requires
    )


def enhanced_contract_findings(source: Path, metadata: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    contract = metadata.get("metadata")
    has_contract = contract is not None
    if has_contract and not isinstance(contract, dict):
        findings.append("frontmatter metadata must be a mapping")

    portability: str | None = None
    requires: list[str] | None = None
    if isinstance(contract, dict):
        portability = contract.get("portability")
        distribution = contract.get("distribution")
        raw_requires = contract.get("requires")
        if portability not in PORTABILITY_VALUES:
            findings.append(
                "metadata.portability must be one of: " + ", ".join(sorted(PORTABILITY_VALUES))
            )
        if distribution not in DISTRIBUTION_VALUES:
            findings.append(
                "metadata.distribution must be one of: " + ", ".join(sorted(DISTRIBUTION_VALUES))
            )
        if not isinstance(raw_requires, list) or any(
            not isinstance(item, str) or not item.strip() for item in raw_requires
        ):
            findings.append("metadata.requires must be a list of non-empty strings")
        elif len(raw_requires) != len(set(raw_requires)):
            findings.append("metadata.requires must not contain duplicates")
        else:
            requires = raw_requires

    openai_path = source / "agents" / "openai.yaml"
    if not openai_path.is_file():
        if has_contract:
            findings.append("missing required file: agents/openai.yaml")
    else:
        try:
            openai = yaml.safe_load(openai_path.read_text(encoding="utf-8-sig"))
        except (OSError, yaml.YAMLError) as exc:
            findings.append(f"invalid agents/openai.yaml: {exc}")
        else:
            policy = openai.get("policy") if isinstance(openai, dict) else None
            actual = policy.get("allow_implicit_invocation") if isinstance(policy, dict) else None
            expected = metadata.get("disable-model-invocation") is not True
            if actual is not expected:
                findings.append(
                    "agents/openai.yaml policy.allow_implicit_invocation must mirror "
                    f"SKILL.md invocation policy ({str(expected).lower()})"
                )

    for markdown in source.rglob("*.md"):
        if "reports" in markdown.relative_to(source).parts:
            continue
        try:
            content = markdown.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(content):
            target = match.group(1).split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not (markdown.parent / target).exists():
                relative = markdown.relative_to(source).as_posix()
                findings.append(f"broken local Markdown link: {relative} -> {target}")

    pollution = []
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            pollution.append(relative.as_posix())
        elif "reports" in relative.parts and path.is_file() and path.name != ".gitkeep":
            pollution.append(relative.as_posix())
    if pollution:
        findings.append("runtime artifacts must stay outside the skill source: " + ", ".join(sorted(pollution)[:10]))

    if portability in PORTABILITY_VALUES and requires is not None:
        couplings = normalized_host_couplings(source)
        if portability == "portable":
            host_requirements = [
                requirement
                for requirement in requires
                if requirement in HOST_REQUIREMENTS
                or requirement.startswith(HOST_REQUIREMENT_PREFIXES)
            ]
            if host_requirements:
                findings.append(
                    "portable skill cannot require host capabilities: "
                    + ", ".join(sorted(host_requirements))
                )
            if couplings:
                findings.append(
                    "portable skill contains host coupling in runtime surfaces: "
                    + ", ".join(sorted(couplings))
                )
        elif couplings and not has_host_requirement(requires):
            findings.append(
                "host-coupled skill metadata.requires must declare a host capability: "
                + ", ".join(sorted(couplings))
            )
        if "workspace-cli" in couplings and "workspace-cli" not in requires:
            findings.append("Workspace CLI coupling requires metadata.requires to include workspace-cli")
        if "workspace-manifest" in couplings and not {"workspace-cli", "workspace-manifest", "optional-workspace-manifest"}.intersection(requires):
            findings.append(
                "Workspace manifest coupling requires metadata.requires to include optional-workspace-manifest"
            )
        if "windows-path" in couplings and not {"windows", "windows-powershell"}.intersection(requires):
            findings.append(
                "Windows path coupling requires metadata.requires to include windows or windows-powershell"
            )
    return findings


def projection_state(link_path: Path, target_path: Path) -> str:
    if not target_path.is_dir():
        return "MISSING_TARGET"
    if not os.path.lexists(link_path):
        return "MISSING"
    try:
        current = os.path.normcase(os.path.abspath(os.path.realpath(link_path)))
        expected = os.path.normcase(os.path.abspath(target_path))
        if current == expected:
            return "OK"
    except OSError:
        pass
    return "BLOCKED_EXISTING_ITEM"


def list_skills(
    manifest: dict[str, Any],
    *,
    platform: str | None = None,
) -> dict[str, Any]:
    root = workspace_root(manifest)
    rows: list[dict[str, Any]] = []
    for skill in manifest.get("skills", []):
        if not isinstance(skill, dict):
            continue
        exposures = [
            exposure
            for exposure in skill.get("exposures", [])
            if isinstance(exposure, dict)
            and (platform is None or str(exposure.get("platform")) == platform)
        ]
        if platform is not None and not exposures:
            continue
        source = resolve_workspace_path(root, str(skill.get("source_path", "")))
        projections: list[dict[str, str]] = []
        for exposure in exposures:
            projection = projection_by_id(manifest, str(exposure.get("projection_id", "")))
            if not projection:
                projections.append(
                    {
                        "platform": str(exposure.get("platform", "")),
                        "projection_id": str(exposure.get("projection_id", "")),
                        "state": "MISSING_MANIFEST_ENTRY",
                    }
                )
                continue
            link = Path(os.path.abspath(str(projection.get("link_path", ""))))
            target = resolve_workspace_path(root, str(projection.get("target_path", "")))
            projections.append(
                {
                    "platform": str(projection.get("platform", "")),
                    "projection_id": str(projection.get("id", "")),
                    "state": projection_state(link, target),
                }
            )
        rows.append(
            {
                "id": str(skill.get("id", "")),
                "role": str(skill.get("role", "")),
                "source_path": str(skill.get("source_path", "")),
                "source_state": "OK" if source.is_dir() else "MISSING",
                "projections": projections,
            }
        )
    return {"status": "PASS", "skills": rows}


def validate_skill(
    manifest: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    root = workspace_root(manifest)
    registered = manifest_skill(manifest, target) or manifest_skill_by_source(
        manifest, target
    )
    source_value = str(registered.get("source_path")) if registered else target
    try:
        source = resolve_workspace_path(root, source_value)
    except ValueError as exc:
        return {"status": "ERROR", "target": target, "findings": [str(exc)]}

    expected_id = str(registered.get("id")) if registered else source.name
    findings: list[str] = []
    warnings: list[str] = []
    if not source.is_dir():
        findings.append(f"missing skill source directory: {source}")
    else:
        skill_md = source / "SKILL.md"
        if not skill_md.is_file():
            findings.append("missing required file: SKILL.md")
        else:
            metadata, error = parse_frontmatter(skill_md)
            if error:
                findings.append(error)
            else:
                name = str(metadata.get("name", "")).strip()
                description = str(metadata.get("description", "")).strip()
                if name != expected_id:
                    findings.append(
                        f"frontmatter name must match skill id '{expected_id}', found '{name}'"
                    )
                if not description:
                    findings.append("frontmatter description must be non-empty")
                if source_path_requires_contract(source_value) and "metadata" not in metadata:
                    findings.append("standalone skill requires frontmatter metadata")
                findings.extend(enhanced_contract_findings(source, metadata))
        if registered:
            for relative in registered.get("required_files", []):
                if not (source / Path(str(relative))).exists():
                    findings.append(f"missing manifest-required file: {relative}")
        else:
            readme = source / "README.md"
            if not readme.is_file():
                warnings.append(
                    "README.md is absent; standalone SKILL.md packages may omit it"
                )
            warnings.append(
                "skill is not registered in workspace_manifest.yaml; validation covered only the source package"
            )

    return {
        "status": "ERROR" if findings else ("WARN" if warnings else "PASS"),
        "target": target,
        "skill_id": expected_id,
        "source_path": str(source),
        "registered": registered is not None,
        "findings": findings,
        "warnings": warnings,
    }


def init_skill(
    manifest: dict[str, Any],
    skill_id: str,
    source_path: str,
    description: str,
) -> dict[str, Any]:
    if not SKILL_ID_PATTERN.fullmatch(skill_id):
        return {
            "status": "ERROR",
            "message": "skill id must use lowercase letters, numbers, and hyphens",
        }
    if manifest_skill(manifest, skill_id):
        return {"status": "BLOCKED", "message": f"skill is already registered: {skill_id}"}
    root = workspace_root(manifest)
    try:
        source = resolve_workspace_path(root, source_path)
    except ValueError as exc:
        return {"status": "BLOCKED", "message": str(exc)}
    if source.exists():
        return {"status": "BLOCKED", "message": f"source path already exists: {source}"}

    files = {
        "SKILL.md": (
            "---\n"
            f"name: {skill_id}\n"
            f"description: {json.dumps(description, ensure_ascii=False)}\n"
            "---\n\n"
            f"# {skill_id}\n\n"
            "## Use When\n\n"
            "- Define the tasks that should trigger this skill.\n\n"
            "## Workflow\n\n"
            "1. Read only the references required for the current task.\n"
            "2. Perform the bounded skill workflow.\n"
            "3. Validate the result before returning it.\n\n"
            "## Boundaries\n\n"
            "- Do not expand authority beyond this skill's declared task contract.\n"
        ),
        "README.md": (
            f"# {skill_id}\n\n"
            f"{description}\n\n"
            "This package is source code. Register it in `workspace_manifest.yaml` "
            "before platform exposure.\n"
        ),
        "references/README.md": "# References\n\nAdd knowledge that should be loaded only when needed.\n",
        "scripts/README.md": "# Scripts\n\nAdd deterministic helpers here when the workflow needs them.\n",
        "tests/README.md": "# Tests\n\nAdd focused structure and behavior tests here.\n",
        "assets/README.md": "# Assets\n\nAdd reusable templates or static assets here.\n",
    }
    for relative, content in files.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {
        "status": "CREATED",
        "skill_id": skill_id,
        "source_path": str(source),
        "created_files": sorted(files),
        "next": [
            "Review and replace the scaffold placeholders.",
            "Register the skill and its projections in workspace_manifest.yaml.",
            f"Run workspace skill validate {skill_id} after registration.",
            f"Run workspace skill expose {skill_id} --platform <platform> before adding --apply.",
        ],
    }


def create_projection(link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link_path), str(target_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or result.stdout.strip())
        return
    os.symlink(target_path, link_path, target_is_directory=True)


def expose_skill(
    manifest: dict[str, Any],
    skill_id: str,
    platform: str | None,
    *,
    apply: bool = False,
    creator: Callable[[Path, Path], None] = create_projection,
) -> dict[str, Any]:
    skill = manifest_skill(manifest, skill_id)
    if not skill:
        return {"status": "ERROR", "message": f"skill is not registered: {skill_id}"}
    exposures = [
        exposure
        for exposure in skill.get("exposures", [])
        if isinstance(exposure, dict)
        and (platform is None or str(exposure.get("platform")) == platform)
    ]
    if not exposures:
        return {
            "status": "ERROR",
            "message": f"no manifest exposure for skill '{skill_id}'"
            + (f" on platform '{platform}'" if platform else ""),
        }
    if platform is None and len(exposures) > 1:
        choices = sorted(str(item.get("platform", "")) for item in exposures)
        return {
            "status": "BLOCKED",
            "message": "multiple platforms are registered; pass --platform",
            "platforms": choices,
        }

    exposure = exposures[0]
    projection_id = str(exposure.get("projection_id", ""))
    projection = projection_by_id(manifest, projection_id)
    if not projection:
        return {
            "status": "ERROR",
            "message": f"missing manifest projection: {projection_id}",
        }
    root = workspace_root(manifest)
    source = resolve_workspace_path(root, str(projection.get("target_path", "")))
    link = Path(os.path.abspath(str(projection.get("link_path", ""))))
    state = projection_state(link, source)
    payload = {
        "status": state,
        "skill_id": skill_id,
        "platform": str(projection.get("platform", "")),
        "projection_id": projection_id,
        "source_path": str(source),
        "link_path": str(link),
        "apply": apply,
    }
    if state == "MISSING_TARGET":
        payload["status"] = "BLOCKED"
        payload["message"] = "manifest-selected source directory is missing"
        return payload
    if state == "OK":
        payload["message"] = "projection already points to the manifest-selected source"
        return payload
    if state == "BLOCKED_EXISTING_ITEM":
        payload["status"] = "BLOCKED"
        payload["message"] = "existing file, directory, or incorrect link was preserved"
        return payload
    if not apply:
        payload["status"] = "PLAN"
        payload["message"] = "projection is missing; rerun with --apply to create it"
        return payload
    try:
        creator(link, source)
    except OSError as exc:
        payload["status"] = "ERROR"
        payload["message"] = f"failed to create projection: {exc}"
        return payload
    payload["status"] = "CREATED"
    payload["message"] = "projection created from manifest"
    return payload


def render(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if "skills" in payload:
        print("Skill Registry")
        for skill in payload["skills"]:
            projection_text = ", ".join(
                f"{item['platform']}={item['state']}" for item in skill["projections"]
            ) or "(none)"
            print(
                f"- {skill['id']}: source={skill['source_state']} "
                f"role={skill['role']} projections={projection_text}"
            )
        return
    print(f"Status: {payload['status']}")
    for key in ("skill_id", "source_path", "platform", "link_path", "message"):
        if payload.get(key):
            print(f"{key.replace('_', ' ').title()}: {payload[key]}")
    for finding in payload.get("findings", []):
        print(f"ERROR: {finding}")
    for warning in payload.get("warnings", []):
        print(f"WARNING: {warning}")
    for item in payload.get("next", []):
        print(f"NEXT: {item}")


def exit_code(payload: dict[str, Any]) -> int:
    if payload.get("status") in {"ERROR", "BLOCKED"}:
        return 1
    if payload.get("status") == "WARN":
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage workspace skill source packages.")
    commands = parser.add_subparsers(dest="action", required=True)

    init = commands.add_parser("init")
    init.add_argument("skill_id")
    init.add_argument("--source-path", required=True)
    init.add_argument("--description", required=True)
    init.add_argument("--format", choices=("text", "json"), default="text")

    validate = commands.add_parser("validate")
    validate.add_argument("target")
    validate.add_argument("--format", choices=("text", "json"), default="text")

    list_parser = commands.add_parser("list")
    list_parser.add_argument("--platform")
    list_parser.add_argument("--format", choices=("text", "json"), default="text")

    expose = commands.add_parser("expose")
    expose.add_argument("skill_id")
    expose.add_argument("--platform")
    expose.add_argument("--apply", action="store_true")
    expose.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = load_manifest()
        if args.action == "init":
            payload = init_skill(
                manifest,
                args.skill_id,
                args.source_path,
                args.description,
            )
        elif args.action == "validate":
            payload = validate_skill(manifest, args.target)
        elif args.action == "list":
            payload = list_skills(manifest, platform=args.platform)
        else:
            payload = expose_skill(
                manifest,
                args.skill_id,
                args.platform,
                apply=args.apply,
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {"status": "ERROR", "message": str(exc)}
    render(payload, args.format)
    return exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
