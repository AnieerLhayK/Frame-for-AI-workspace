from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from scripts.publishing import sync_public_projections as sync
from scripts.publishing import workspace_state


def test_registered_publishers_are_discovered_from_policy(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "sync_demo.py"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    policy = {"managed_platform_publishers": {"demo": {"publisher_script": "scripts/sync_demo.py"}}}

    with patch.object(sync, "WORKSPACE_ROOT", tmp_path):
        assert sync.registered_publishers(policy) == {"demo": "scripts/sync_demo.py"}


def test_registered_publishers_include_every_registered_entry(tmp_path: Path) -> None:
    first = tmp_path / "scripts" / "sync_first.py"
    second = tmp_path / "scripts" / "sync_second.py"
    first.parent.mkdir(parents=True)
    first.write_text("", encoding="utf-8")
    second.write_text("", encoding="utf-8")
    policy = {
        "managed_platform_publishers": {
            "first": {"publisher_script": "scripts/sync_first.py"},
            "second": {"publisher_script": "scripts/sync_second.py"},
        }
    }

    with patch.object(sync, "WORKSPACE_ROOT", tmp_path):
        assert sync.registered_publishers(policy) == {
            "first": "scripts/sync_first.py",
            "second": "scripts/sync_second.py",
        }


def test_integrated_main_error_requires_head_and_remote_main_to_match() -> None:
    assert sync.integrated_main_error("abc", "abc", "abc") is None
    assert "HEAD" in sync.integrated_main_error("def", "abc", "abc")
    assert "origin/main" in sync.integrated_main_error("abc", "abc", "def")


def test_sync_forwards_registered_publisher_arguments() -> None:
    commands: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object):
        commands.append(command)
        return type("Result", (), {"returncode": 0})()

    assert sync.sync_publishers(
        {"frame": "scripts/publishing/sync_public_repo.py"},
        [],
        record_id="TASK-20260723-004",
        agent="codex",
        push=True,
        skip_tests=True,
        runner=runner,
    ) == 0
    assert commands[0] == [
        sync.sys.executable,
        "-m",
        "scripts.publishing.sync_public_repo",
        "--record-id",
        "TASK-20260723-004",
        "--agent",
        "codex",
        "--skip-tests",
        "--push",
    ]


def test_parser_rejects_unknown_publisher() -> None:
    parser = sync.build_parser(["frame"])
    try:
        parser.parse_args(["--record-id", "TASK-20260723-004", "--publisher", "unknown"])
    except SystemExit:
        return
    raise AssertionError("unknown publisher was accepted")


def test_workspace_clean_allows_only_the_exact_untracked_record(monkeypatch, tmp_path: Path) -> None:
    record_id = "TASK-20260830-010"
    expected = "PROJECT_CONTEXT/tasks/records/2026/08/30/TASK-20260830-010.json"

    def status(stdout: str):
        return subprocess.CompletedProcess(["git"], 0, stdout=stdout, stderr="")

    monkeypatch.setattr(workspace_state.subprocess, "run", lambda *args, **kwargs: status(f"?? {expected}\0"))
    assert workspace_state.workspace_clean_for_record(tmp_path, record_id)

    monkeypatch.setattr(workspace_state.subprocess, "run", lambda *args, **kwargs: status("?? unrelated.txt\0"))
    assert not workspace_state.workspace_clean_for_record(tmp_path, record_id)


def test_workspace_clean_rejects_staged_or_invalid_record_state(monkeypatch, tmp_path: Path) -> None:
    expected = "PROJECT_CONTEXT/tasks/records/2026/08/30/TASK-20260830-010.json"

    monkeypatch.setattr(
        workspace_state.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            ["git"], 0, stdout=f"M  {expected}\0", stderr=""
        ),
    )
    assert not workspace_state.workspace_clean_for_record(tmp_path, "TASK-20260830-010")
    assert not workspace_state.workspace_clean_for_record(tmp_path, "bad-record")


def test_workspace_clean_accepts_clean_or_exact_unstaged_record(monkeypatch, tmp_path: Path) -> None:
    expected = "PROJECT_CONTEXT/tasks/records/2026/08/30/TASK-20260830-010.json"

    for output in ("", f" M {expected}\0"):
        monkeypatch.setattr(
            workspace_state.subprocess,
            "run",
            lambda *args, _output=output, **kwargs: subprocess.CompletedProcess(
                ["git"], 0, stdout=_output, stderr=""
            ),
        )
        assert workspace_state.workspace_clean_for_record(tmp_path, "TASK-20260830-010")


def test_workspace_clean_rejects_git_status_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        workspace_state.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(["git"], 1, stdout="", stderr="failed"),
    )
    assert not workspace_state.workspace_clean_for_record(tmp_path, "TASK-20260830-010")
