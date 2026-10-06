import json
import hashlib
from pathlib import Path
import subprocess

import pytest

from scripts.publishing import sync_ai_workbench_repo as publisher
from scripts.publishing import registered_repo_sync as sync


@pytest.fixture
def package_source():
    source = Path(__file__).resolve().parents[3] / "packages/ai-workbench"
    if not (source / "scripts/projection.py").is_file():
        pytest.skip("Frame excludes this package; verify its owning ai-workbench projection instead")
    return source


def result(stdout="", code=0):
    return subprocess.CompletedProcess([], code, stdout=stdout, stderr="failure" if code else "")


def test_empty_remote_initialization_without_workspace_history(monkeypatch, tmp_path):
    calls = []
    staging = tmp_path / "repo"

    def git(command, cwd=None, **kwargs):
        calls.append(command)
        if command[1] == "clone":
            (staging / ".git").mkdir(parents=True)
        if command[1:3] == ["rev-parse", "--verify"]:
            return result(code=1)
        return result()

    monkeypatch.setattr(sync, "run_git", git)
    sync.prepare_initializable_staging(staging, "registered", lambda *_: pytest.fail("empty baseline"))
    assert ["git", "symbolic-ref", "HEAD", "refs/heads/main"] in calls
    assert not any(command[1] in {"reset", "clean", "fetch"} for command in calls)


def test_remote_inspection_failure_is_not_empty(monkeypatch, tmp_path):
    calls = []

    def git(command, *args, **kwargs):
        calls.append(command)
        return result(code=1)

    monkeypatch.setattr(sync, "run_git", git)
    with pytest.raises(RuntimeError, match="failure"):
        sync.prepare_initializable_staging(tmp_path / "repo", "registered", lambda *_: None)
    assert len(calls) == 1


def test_wrong_existing_origin_never_repointed(monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    calls = []

    def git(command, *args, **kwargs):
        calls.append(command)
        return result("other")

    monkeypatch.setattr(sync, "run_git", git)
    with pytest.raises(RuntimeError, match="origin"):
        sync.prepare_initializable_staging(tmp_path, "registered", lambda *_: None)
    assert len(calls) == 1


def test_nonempty_unknown_remote_stops_before_reset(monkeypatch, tmp_path):
    calls = []

    def git(command, *args, **kwargs):
        calls.append(command)
        if command[1] == "ls-remote":
            return result("abc\trefs/heads/main\n")
        if command[1] == "clone":
            (tmp_path / "repo" / ".git").mkdir(parents=True)
        return result()

    monkeypatch.setattr(sync, "run_git", git)

    def unrecognized(*args):
        raise RuntimeError("audit required")

    with pytest.raises(RuntimeError, match="audit"):
        sync.prepare_initializable_staging(tmp_path / "repo", "registered", unrecognized)
    assert not any(command[1] in {"reset", "clean", "rm"} for command in calls)


def test_nonempty_remote_requires_main(monkeypatch, tmp_path):
    monkeypatch.setattr(sync, "run_git", lambda *a, **kw: result("abc\trefs/heads/other\n"))
    with pytest.raises(RuntimeError, match="expected branch"):
        sync.prepare_initializable_staging(tmp_path / "repo", "registered", lambda *_: None)


def test_recognized_baseline_verified_before_reset(monkeypatch, tmp_path):
    calls = []
    (tmp_path / ".git").mkdir()

    def git(command, *args, **kwargs):
        calls.append(command)
        if command[1:3] == ["remote", "get-url"]:
            return result("registered")
        if command[1] == "ls-remote":
            return result("abc\trefs/heads/main\n")
        return result()

    monkeypatch.setattr(sync, "run_git", git)
    sync.prepare_initializable_staging(tmp_path, "registered", lambda *_: calls.append(["verified"]))
    assert calls.index(["verified"]) < calls.index(["git", "reset", "--hard", "origin/main"])


def test_remote_provenance_rejects_private_fields(monkeypatch, tmp_path, package_source):
    projection = publisher.projection_module(package_source)
    marker = projection.provenance("a" * 40)
    marker["private_url"] = "secret"
    monkeypatch.setattr(sync, "run_git", lambda *a, **kw: result(json.dumps(marker)))
    with pytest.raises(RuntimeError, match="audit"):
        publisher.verify_baseline(tmp_path, "origin/main", projection)


@pytest.mark.parametrize("drift", [None, "extra", "modified", "unknown_revision"])
def test_baseline_matches_referenced_authoritative_export(monkeypatch, tmp_path, drift, package_source):
    projection = publisher.projection_module(package_source)
    marker = projection.provenance("a" * 40)
    contract = {"files": ["README.md", "projection-contract.json"], "generated_files": projection.GENERATED}
    payload = (json.dumps(marker, indent=2) + "\n").encode()
    marker_hash = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    remote = f"100644 blob readme\tREADME.md\0" + f"100644 blob contract\tprojection-contract.json\0" + f"100644 blob {marker_hash}\tPROJECTION_SOURCE.json\0"
    if drift == "extra":
        remote += "100644 blob secret\tprivate.json\0"
    if drift == "modified":
        remote = remote.replace("blob readme", "blob modified")

    def git(command, cwd=None, **kwargs):
        if command[1] == "merge-base":
            return result(code=1 if drift == "unknown_revision" else 0)
        if command[1] == "show":
            return result(json.dumps(marker if cwd == tmp_path else contract))
        if command[1] == "ls-tree":
            if cwd == tmp_path:
                return result(remote)
            return result("100644 blob readme\tpackages/ai-workbench/README.md\0" + "100644 blob contract\tpackages/ai-workbench/projection-contract.json\0")
        pytest.fail(f"Unexpected command {command}")

    monkeypatch.setattr(sync, "run_git", git)
    if drift:
        with pytest.raises(RuntimeError, match="audit"):
            publisher.verify_baseline(tmp_path, "origin/main", projection)
    else:
        publisher.verify_baseline(tmp_path, "origin/main", projection)


def test_authorization_precedes_external_operations(monkeypatch):
    monkeypatch.setattr(publisher, "load_yaml", lambda *_: {})
    monkeypatch.setattr(publisher, "config", lambda *_: (Path("source"), Path("staging"), "registered"))
    monkeypatch.setattr(sync, "require_managed_publish_authorization", lambda **kw: (_ for _ in ()).throw(ValueError("denied")))
    monkeypatch.setattr(sync, "prepare_initializable_staging", lambda *_: pytest.fail("unauthorized prepare"))
    monkeypatch.setattr(sync, "cleanup_staging", lambda *_: pytest.fail("unauthorized cleanup"))
    assert publisher.main(["--record-id", "TASK-test", "--push"]) == 1


def test_push_failure_preserves_staging(monkeypatch, tmp_path, package_source):
    source = package_source
    monkeypatch.setattr(publisher, "load_yaml", lambda *_: {})
    monkeypatch.setattr(publisher, "config", lambda *_: (source, tmp_path, "registered"))
    monkeypatch.setattr(sync, "require_managed_publish_authorization", lambda **kw: None)
    monkeypatch.setattr(publisher, "workspace_clean_for_record", lambda *_: True)
    monkeypatch.setattr(sync, "run_git", lambda *a, **kw: result("a" * 40))
    monkeypatch.setattr(sync, "prepare_initializable_staging", lambda *_: None)
    monkeypatch.setattr(publisher, "verify_export", lambda *a, **kw: None)
    monkeypatch.setattr(sync, "commit_and_push", lambda *_: (_ for _ in ()).throw(RuntimeError("push rejected")))
    monkeypatch.setattr(sync, "cleanup_staging", lambda *_: pytest.fail("failed staging must remain"))
    assert publisher.main(["--record-id", "TASK-test", "--push"]) == 1
    assert (tmp_path / "checkout" / "PROJECTION_SOURCE.json").is_file()


def test_registered_config_and_dispatch(package_source):
    from scripts.publishing.sync_public_projections import registered_publishers
    policy = publisher.load_yaml(publisher.POLICY_PATH)
    source, staging, remote = publisher.config(policy)
    assert source.name == "ai-workbench"
    assert staging.name == "ai-workbench-public"
    assert remote == "git@github.com:AnieerLhayK/ai-workbench.git"
    assert registered_publishers(policy)["ai_workbench"] == publisher.PUBLISHER_SCRIPT
