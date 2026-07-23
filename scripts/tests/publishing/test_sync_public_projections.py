from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.publishing import sync_public_projections as sync


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
        {"frame": "scripts/sync_public_repo.py"},
        [],
        record_id="TASK-20260723-004",
        agent="codex",
        push=True,
        skip_tests=True,
        runner=runner,
    ) == 0
    assert commands[0][-6:] == ["--record-id", "TASK-20260723-004", "--agent", "codex", "--skip-tests", "--push"]


def test_parser_rejects_unknown_publisher() -> None:
    parser = sync.build_parser(["frame"])
    try:
        parser.parse_args(["--record-id", "TASK-20260723-004", "--publisher", "unknown"])
    except SystemExit:
        return
    raise AssertionError("unknown publisher was accepted")
