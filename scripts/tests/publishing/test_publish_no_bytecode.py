from __future__ import annotations

from pathlib import Path

from scripts.publishing.publish_check import _python_check_env, check_no_python_bytecode


def test_python_check_env_disables_bytecode_writes(monkeypatch) -> None:
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "0")

    assert _python_check_env()["PYTHONDONTWRITEBYTECODE"] == "1"


def test_bytecode_check_rejects_pycache_and_standalone_pyc(tmp_path: Path) -> None:
    cache = tmp_path / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.pyc").write_bytes(b"bytecode")
    (tmp_path / "orphan.pyc").write_bytes(b"bytecode")

    issues = check_no_python_bytecode(tmp_path)

    assert any("Python bytecode cache exists: scripts/__pycache__/" in issue for issue in issues)
    assert any("Python bytecode file exists: orphan.pyc" in issue for issue in issues)


def test_bytecode_check_allows_clean_tree_and_ignores_git_metadata(tmp_path: Path) -> None:
    (tmp_path / ".git" / "objects" / "__pycache__").mkdir(parents=True)

    assert check_no_python_bytecode(tmp_path) == []
