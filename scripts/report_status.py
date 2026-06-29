from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ReportSpec:
    report_id: str
    paths: tuple[str, ...]
    sources: tuple[str, ...]


@dataclass
class ReportResult:
    report_id: str
    status: str
    paths: list[str]
    generated_at: str | None
    source_commit: str | None
    reasons: list[str]


REPORT_SPECS = (
    ReportSpec(
        report_id="manifest-validation",
        paths=("reports/manifest_validation_report.md",),
        sources=(
            "workspace_manifest.yaml",
            "shared",
            "scripts/validate_manifest.py",
        ),
    ),
    ReportSpec(
        report_id="protocol-validation",
        paths=("reports/protocol_validation_report.md",),
        sources=(
            "workspace_manifest.yaml",
            "shared",
            "packages/character-system/shared",
            "packages/character-system/engineering/generation/character-generator/SHARED_PROTOCOLS.md",
            "packages/character-system/engineering/maintenance/character-maintainer/SHARED_PROTOCOLS.md",
            "packages/character-system/engineering/diagnosis/style-doctor/SHARED_PROTOCOLS.md",
            "packages/character-system/runtime/characters/zyc/SHARED_PROTOCOLS.md",
            "scripts/validate_protocols.py",
        ),
    ),
    ReportSpec(
        report_id="workspace",
        paths=(
            "reports/workspace_setup_report.md",
            "reports/workspace_health_report.md",
        ),
        sources=(
            "workspace_manifest.yaml",
            "shared",
            "packages/character-system",
            "scripts/sync_report.ps1",
        ),
    ),
)


def parse_header(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    header: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        header[key.strip()] = value.strip()
    return header


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from (item for item in path.rglob("*") if item.is_file())


def newest_source(root: Path, sources: tuple[str, ...]) -> tuple[Path | None, float]:
    newest_path: Path | None = None
    newest_mtime = 0.0
    for relative in sources:
        for path in iter_files(root / relative):
            mtime = path.stat().st_mtime
            if mtime > newest_mtime:
                newest_path = path
                newest_mtime = mtime
    return newest_path, newest_mtime


def current_commit(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def last_change_commit(root: Path, paths: Iterable[str]) -> str | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", *paths],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def has_working_tree_changes(root: Path, paths: Iterable[str]) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def is_ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def git_staleness_reason(spec: ReportSpec, root: Path) -> str | None:
    report_commit = last_change_commit(root, spec.paths)
    source_commit = last_change_commit(root, spec.sources)
    if not report_commit or not source_commit:
        return None
    if is_ancestor(root, source_commit, report_commit):
        return None
    return (
        "relevant source commit is newer than report commit: "
        f"source={source_commit[:7]}, report={report_commit[:7]}"
    )


def assess_report(
    spec: ReportSpec,
    root: Path,
    commit: str | None,
) -> ReportResult:
    report_paths = [root / relative for relative in spec.paths]
    missing = [path for path in report_paths if not path.is_file()]
    reasons: list[str] = []
    if missing:
        reasons.extend(f"missing report: {path.relative_to(root).as_posix()}" for path in missing)
        return ReportResult(spec.report_id, "MISSING", list(spec.paths), None, None, reasons)

    headers = [parse_header(path) for path in report_paths]
    if any(not header for header in headers):
        reasons.append("one or more reports lack a readable snapshot header")

    generated_values = {header.get("generated_at") for header in headers}
    source_commits = {header.get("source_commit") for header in headers}
    generated_at = next(iter(generated_values)) if len(generated_values) == 1 else None
    source_commit = next(iter(source_commits)) if len(source_commits) == 1 else None
    if len(generated_values) != 1:
        reasons.append("grouped reports have different generation timestamps")
    if len(source_commits) != 1:
        reasons.append("grouped reports have different source commits")
    report_has_working_tree_changes = has_working_tree_changes(root, spec.paths)
    git_reason = None if report_has_working_tree_changes else git_staleness_reason(spec, root)
    if git_reason:
        reasons.append(git_reason)
    elif not source_commit:
        reasons.append("one or more reports lack a source_commit header")

    newest_path, newest_mtime = newest_source(root, spec.sources)
    oldest_report_mtime = min(path.stat().st_mtime for path in report_paths)
    if newest_path and newest_mtime > oldest_report_mtime:
        reasons.append(
            f"source is newer than report: {newest_path.relative_to(root).as_posix()}"
        )

    status = "STALE" if reasons else "FRESH"
    return ReportResult(
        spec.report_id,
        status,
        list(spec.paths),
        generated_at,
        source_commit,
        reasons,
    )


def render_text(results: list[ReportResult]) -> None:
    for result in results:
        print(f"{result.report_id}: {result.status}")
        print(f"  reports: {', '.join(result.paths)}")
        if result.generated_at:
            print(f"  generated_at: {result.generated_at}")
        if result.source_commit:
            print(f"  source_commit: {result.source_commit}")
        for reason in result.reasons:
            print(f"  reason: {reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check snapshot report freshness without writing files.")
    parser.add_argument(
        "--report-id",
        choices=tuple(spec.report_id for spec in REPORT_SPECS),
        action="append",
        default=[],
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when any selected report is stale or missing.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selected = set(args.report_id)
    specs = [spec for spec in REPORT_SPECS if not selected or spec.report_id in selected]
    commit = current_commit(WORKSPACE_ROOT)
    results = [assess_report(spec, WORKSPACE_ROOT, commit) for spec in specs]

    if args.format == "json":
        print(
            json.dumps(
                {
                    "workspace_root": str(WORKSPACE_ROOT),
                    "current_commit": commit,
                    "reports": [asdict(result) for result in results],
                },
                indent=2,
            )
        )
    else:
        render_text(results)

    if args.strict and any(result.status != "FRESH" for result in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
