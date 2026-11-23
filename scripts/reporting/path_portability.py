"""Classify bounded Git-index path references without rewriting evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {".cfg", ".css", ".csv", ".html", ".ini", ".js", ".json", ".md", ".ps1", ".py", ".toml", ".ts", ".txt", ".xml", ".yaml", ".yml"}


def catalog_files(root: Path, manifest: dict) -> set[str]:
    files = set()
    for relative in manifest.get("skill_catalogs", {}).values():
        index = root / relative / "catalog.json"
        for category in json.loads(index.read_text(encoding="utf8"))["categories"]:
            files.add((Path(relative) / category).as_posix())
    files.update(p["package_catalog"] for p in manifest.get("packages", []) if "package_catalog" in p)
    return files


def classify_reference(relative: str, content: str, token: str, catalogs: set[str]) -> tuple[str, str, bool]:
    path = relative.replace("\\", "/")
    if path == "workspace_manifest.yaml":
        return "manifest-source-of-truth", "Deployment facts; field validity checked by manifest validator", False
    if path in catalogs:
        payload = json.loads(content)
        fields = []
        def walk(value, key=""):
            if isinstance(value, dict):
                for name, child in value.items(): walk(child, name)
            elif isinstance(value, list):
                for child in value: walk(child, key)
            elif isinstance(value, str) and token.replace("\\\\", "\\") in value:
                fields.append(key)
        walk(payload)
        if fields and all(key in {"projection_path", "link_path"} for key in fields):
            return "catalog-deployment", "Manifest-loaded projection aliases, not internal source paths", False
    evidence = Path(path).suffix.lower() in {".md", ".json", ".csv", ".txt"}
    report_root = path.startswith("reports/") or (path.startswith("packages/") and "/reports/" in path)
    if evidence and report_root and not Path(path).name.lower().startswith("readme"):
        return "report-evidence", "Snapshot or review evidence, not an active path default", False
    if evidence and (path.startswith(("PROJECT_CONTEXT/tasks/records/", "PROJECT_CONTEXT/tasks/ledger/", "PROJECT_CONTEXT/reports/history/", "WORKSPACE_ENGINEERING/evidence/", "WORKSPACE_ENGINEERING/proposals/")) or path == "PROJECT_CONTEXT/continuity/session_migrations.json"):

        return "historical-evidence", "Preserve original recorded deployment paths", False
    if path.startswith("scripts/tests/"):
        return "test-fixture", "Regression inputs and assertions, not production defaults", False
    lines = [line.strip() for line in content.splitlines() if token in line]
    if path == "scripts/publishing/publish_policy.py" and lines and all(line.startswith("(re.escape(") for line in lines):
        return "migration-signature", "Exact legacy-path replacement signatures must retain source spellings", False
    if path == "scripts/publishing/publish_check_skill_collection.py" and lines and all(line.startswith("FORBIDDEN_TEXT =") for line in lines):
        return "security-signature", "Public leak detector needs exact forbidden path signatures", False
    return "source-review", "Unexplained active reference: derive from manifest or review with owner", True


def collect_findings(root: Path, manifest: dict) -> list[dict]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"], capture_output=True, check=True)
    tokens = {str(manifest["workspace"]["source_of_truth"]), *map(str, manifest.get("platform_roots", {}).values())}
    tokens |= {t.replace("\\", "\\\\") for t in tokens}
    catalogs = catalog_files(root, manifest)
    findings = []
    for relative in sorted(set(result.stdout.decode("utf8").split("\0")) - {""}):
        file = root / relative
        if file.suffix.lower() not in TEXT_EXTENSIONS or not file.is_file() or file.stat().st_size > 2 * 1024 * 1024:
            continue
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            continue
        content = file.read_text(encoding="utf-8-sig", errors="replace")
        for token in sorted(tokens):
            if token and token in content:
                category, reason, review = classify_reference(relative, content, token, catalogs)
                findings.append({"File": relative, "Token": token, "Category": category, "Reason": reason, "RequiresReview": review})
    return findings


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.workspace.manifest_loader import load_manifest
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    print(json.dumps(collect_findings(root, load_manifest(args.manifest or root / "workspace_manifest.yaml")), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
