"""Read-only drift checks for reviewed harness-profile sources."""
from __future__ import annotations

import difflib
import hashlib
import argparse
import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import yaml

from scripts.workspace.runtime import WORKSPACE_ROOT


MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_DIFF_CHARS = 50000
SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
OFFICIAL_HOSTS = {"developers.openai.com", "platform.openai.com", "learn.chatgpt.com", "code.claude.com"}


def _official_url(value: str) -> bool:
    parsed = urlsplit(value)
    return (parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS and
            parsed.username is None and parsed.password is None and parsed.port in (None, 443))


class _OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _official_url(newurl):
            raise ValueError("harness source redirected outside approved official hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_official(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Workspace-Harness-Source-Check/1"})
    with build_opener(_OfficialRedirect()).open(request, timeout=20) as response:
        data = response.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("harness source exceeds size limit")
    return data.decode("utf-8-sig")


def _read_text(path: Path) -> str:
    with path.open("rb") as stream:
        data = stream.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("harness source exceeds size limit")
    return data.decode("utf-8-sig")


def _source_text(entry: dict[str, Any], root: Path, source_id: str, *, online: bool,
                 fetcher: Callable[[str], str]) -> tuple[str, str | None]:
    if entry.get("kind") == "local":
        value = entry.get("path")
        if not isinstance(value, str) or not value or Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
            raise ValueError(f"invalid local harness source: {source_id}")
        path = (root / value).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"harness source escapes workspace: {source_id}")
        return value, _read_text(path)
    if entry.get("kind") == "url":
        value = entry.get("url")
        if not isinstance(value, str) or not _official_url(value):
            raise ValueError(f"unapproved harness source URL: {source_id}")
        if not online:
            return value, None
        current = fetcher(value)
        if not isinstance(current, str) or len(current.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError(f"invalid remote harness source: {source_id}")
        return value, current
    raise ValueError(f"unsupported harness source kind: {source_id}")


def capture_candidates(catalog: dict[str, Any], root: Path, *,
                       fetcher: Callable[[str], str] = _fetch_official) -> dict[str, Any]:
    """Capture source text for a pending-review baseline; do not write or activate it."""
    entries = catalog.get("sources")
    if not isinstance(entries, list) or not entries:
        raise ValueError("harness catalog must contain sources")
    root = root.resolve()
    sources: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid harness source")
        source_id = entry.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id) or source_id in sources:
            raise ValueError("invalid or duplicate harness source id")
        _, current = _source_text(entry, root, source_id, online=True, fetcher=fetcher)
        assert current is not None
        sources[source_id] = current
    return {"status": "pending_review", "sources": sources, "activation_performed": False}


def check_sources(catalog: dict[str, Any], root: Path, baseline: Path, *, online: bool = False,
                  fetcher: Callable[[str], str] = _fetch_official) -> dict[str, Any]:
    """Compare named sources with reviewed snapshots without modifying either."""
    entries = catalog.get("sources")
    if not isinstance(entries, list) or not entries:
        raise ValueError("harness catalog must contain sources")
    root, baseline = root.resolve(), baseline.resolve()
    review_path = (baseline / "review.json").resolve()
    if not review_path.is_relative_to(baseline):
        raise ValueError("review marker escapes baseline")
    try:
        review = json.loads(_read_text(review_path))
    except (FileNotFoundError, json.JSONDecodeError):
        review = {}
    reviewed_sources = review.get("sources", {}) if isinstance(review, dict) and review.get("status") == "reviewed" else {}
    if not isinstance(reviewed_sources, dict):
        reviewed_sources = {}
    seen: set[str] = set()
    rows = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid harness source")
        source_id = entry.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id) or source_id in seen:
            raise ValueError("invalid or duplicate harness source id")
        seen.add(source_id)
        snapshot = (baseline / f"{source_id}.txt").resolve()
        if not snapshot.is_relative_to(baseline):
            raise ValueError(f"reviewed snapshot escapes baseline: {source_id}")
        previous = _read_text(snapshot) if snapshot.is_file() else None
        expected_hash = reviewed_sources.get(source_id)
        reviewed = (previous is not None and isinstance(expected_hash, str) and
                    bool(re.fullmatch(r"[0-9a-f]{64}", expected_hash)) and
                    hashlib.sha256(previous.encode("utf-8")).hexdigest() == expected_hash)
        value, current = _source_text(entry, root, source_id, online=online, fetcher=fetcher)
        if current is None:
            rows.append({"id": source_id, "path": value, "status": "NOT_CHECKED" if reviewed else "UNREVIEWED", "reviewed": reviewed, "diff": ""})
            continue
        row = {"id": source_id, "path": value, "reviewed": reviewed, "current_sha256": hashlib.sha256(current.encode("utf-8")).hexdigest()}
        if previous is None:
            row.update(status="UNREVIEWED", diff="")
        else:
            changed = previous != current
            diff = "".join(difflib.unified_diff(previous.splitlines(keepends=True), current.splitlines(keepends=True),
                                                fromfile=f"reviewed/{source_id}", tofile=f"current/{source_id}"))
            row.update(status=("CHANGED" if changed else "UNCHANGED") if reviewed else "UNREVIEWED", changed=changed, diff=diff[:MAX_DIFF_CHARS],
                       diff_truncated=len(diff) > MAX_DIFF_CHARS)
        rows.append(row)
    states = {row["status"] for row in rows}
    return {"status": "UNREVIEWED" if "UNREVIEWED" in states else "CHANGED" if "CHANGED" in states else "NOT_CHECKED" if "NOT_CHECKED" in states else "UNCHANGED",
            "sources": rows, "baseline_modified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare reviewed harness source snapshots without modifying them.")
    parser.add_argument("action", choices=("check",))
    parser.add_argument("--root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--catalog", type=Path, default=WORKSPACE_ROOT / "WORKSPACE_ENGINEERING/methods/harness_profiles/sources.yaml")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--online", action="store_true", help="Fetch only approved official HTTPS sources.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        catalog = yaml.safe_load(_read_text(args.catalog))
        if not isinstance(catalog, dict):
            raise ValueError("invalid harness source catalog")
        payload = check_sources(catalog, args.root, args.baseline, online=args.online)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        payload = {"status": "ERROR", "message": str(exc), "baseline_modified": False}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {payload['status']}")
        if payload.get("message"):
            print(payload["message"])
        for row in payload.get("sources", []):
            print(f"{row['id']}: {row['status']}")
            if row.get("diff"):
                print(row["diff"])
    return 0 if payload["status"] == "UNCHANGED" else 1 if payload["status"] == "ERROR" else 2


if __name__ == "__main__":
    raise SystemExit(main())
