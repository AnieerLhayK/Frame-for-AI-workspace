from pathlib import Path
import pytest
import os
import json
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripts.workspace.deepseek_workspace_guard import decision


def test_only_scoped_file_tools_and_valid_task_can_write(tmp_path):
    project = tmp_path / "packages" / "ai-workbench"
    project.mkdir(parents=True)
    target = project / "app.py"
    calls = []
    def authorize(path, record, session):
        calls.append((path, record, session))
        return record == "TASK-valid" and session == "session-1"

    request = {"name": "write", "arguments": {"file_path": str(target), "content": "ok"}}
    assert decision(request, tmp_path, "TASK-valid", "session-1", authorize) is None
    assert calls == [(target, "TASK-valid", "session-1")]
    assert decision(request, tmp_path, "TASK-invalid", "session-1", authorize)
    assert decision({"name": "pwsh", "arguments": {"command": "echo x"}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": "packages/ai-workbench/app.py"}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": str(tmp_path / "shared/governance/agent_registry.yaml")}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": str(project / "AGENTS.md")}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": str(project / "AGENTS.md:stream")}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": str(project / "AGENTS.md.")}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "read", "arguments": {"file_path": str(project / ".env.local")}}, tmp_path, "TASK-valid", "session-1", authorize)
    assert decision({"name": "write", "arguments": {"file_path": str(project / "memory" / "notes.md")}}, tmp_path, "TASK-valid", "session-1", authorize)


def test_directory_listing_is_bounded_to_project_and_excludes_sensitive_trees(tmp_path):
    from scripts.workspace.deepseek_workspace_guard import list_entries
    project = tmp_path / "packages" / "ai-workbench"
    project.mkdir(parents=True)
    (project / "src").mkdir()
    (project / "node_modules").mkdir()
    (project / ".secret").write_text("private", encoding="utf-8")
    allowed = {"name": "workspace_list", "arguments": {"path": str(project)}}
    assert decision(allowed, tmp_path, "t", "s", lambda *_: False) is None
    assert decision({"name": "workspace_list", "arguments": {"path": str(tmp_path)}}, tmp_path, "t", "s", lambda *_: True)
    assert decision({"name": "workspace_list", "arguments": {"path": str(project / "node_modules")}}, tmp_path, "t", "s", lambda *_: True)
    assert list_entries(project) == {"entries": [{"name": "src", "type": "directory"}], "truncated": False}


def test_denies_links_and_sandbox_escalation(tmp_path, monkeypatch):
    project = tmp_path / "packages" / "ai-workbench"
    project.mkdir(parents=True)
    target = project / "file.py"
    allow = lambda *_: True
    assert decision({"name": "write", "arguments": {"file_path": str(target), "sandbox_permissions": "require_escalated"}}, tmp_path, "t", "s", allow)
    assert decision({"name": "write", "arguments": {"file_path": str(project / ".." / ".." / "secret")}}, tmp_path, "t", "s", allow)
    skill = tmp_path / "external-skills" / "engineering" / "tdd" / "SKILL.md"
    assert decision({"name": "read", "arguments": {"file_path": str(skill)}}, tmp_path, "t", "s", allow)
    monkeypatch.setenv("DSH_ACTING_SKILL", "tdd")
    assert decision({"name": "read", "arguments": {"file_path": str(skill)}}, tmp_path, "t", "s", allow) is None
    assert decision({"name": "read", "arguments": {"file_path": str(project / "skills" / "unknown" / "SKILL.md")}}, tmp_path, "t", "s", allow)
    unknown = project / "skills" / "unknown"
    unknown.mkdir(parents=True)
    (unknown / "SKILL.md").write_text("instructions", encoding="utf-8")
    (unknown / "README.md").write_text("more instructions", encoding="utf-8")
    assert decision({"name": "read", "arguments": {"file_path": str(unknown / "README.md")}}, tmp_path, "t", "s", allow)
    assert decision({"name": "workspace_list", "arguments": {"path": str(unknown)}}, tmp_path, "t", "s", allow)
    assert decision({"name": "write", "arguments": {"file_path": str(skill)}}, tmp_path, "t", "s", allow)
    original = tmp_path / "outside.txt"
    original.write_text("private", encoding="utf-8")
    hardlink = project / "alias.txt"
    try:
        os.link(original, hardlink)
    except OSError:
        pass
    else:
        assert decision({"name": "write", "arguments": {"file_path": str(hardlink)}}, tmp_path, "t", "s", allow)
        assert decision({"name": "read", "arguments": {"file_path": str(hardlink)}}, tmp_path, "t", "s", allow)
    link = project / "alias"
    try:
        link.symlink_to(project, target_is_directory=True)
    except OSError:
        return  # Windows may not grant symlink creation to this test user.
    assert decision({"name": "write", "arguments": {"file_path": str(link / "file.py")}}, tmp_path, "t", "s", allow)


def test_launcher_rejects_unowned_or_expired_task_before_starting_runtime(tmp_path):
    from scripts.workspace.deepseek_workspace_guard import validate_launch
    project = tmp_path / "packages" / "ai-workbench"
    project.mkdir(parents=True)
    def read(_):
        return None, {"status": "in_progress", "owner": {"agent": "codex", "session_id": "x"},
                      "registration": {"operations": ["workspace_write"]}}
    with pytest.raises(ValueError, match="DeepSeek"):
        validate_launch(project, tmp_path, "TASK-20261107-001", "x", record_reader=read)


def test_actual_registry_denies_unpromoted_deepseek_write():
    from scripts.workspace.deepseek_workspace_guard import authorized
    assert not authorized(Path(__file__), "TASK-20261107-008", "wrong-session")


def test_acting_skill_is_checked_for_each_write(monkeypatch, tmp_path):
    from scripts.workspace import deepseek_workspace_guard as guard
    monkeypatch.setenv("DSH_ACTING_SKILL", "style-doctor")
    monkeypatch.setattr(guard, "read_record", lambda _: (None, {"owner": {"agent": "deepseek-harness-workspace", "session_id": "session"}}))
    monkeypatch.setattr(guard, "load_yaml", lambda _: {})
    monkeypatch.setattr(guard, "load_manifest", lambda: {})
    monkeypatch.setattr(guard, "load_registry", lambda: {})
    seen = []
    def check(*_, **values):
        seen.append(values["acting_skill"])
        return {"status": "DENY"}
    monkeypatch.setattr(guard, "check_task_write", check)
    assert not guard.authorized(tmp_path / "file", "TASK-test", "session")
    assert seen == ["style-doctor"]


def test_guarded_registration_limits_source_writes():
    from scripts.workspace.agent_governance import check_access, load_manifest, load_registry, load_yaml, POLICY_PATH
    from pathlib import Path
    import tempfile
    policy, manifest, registry = load_yaml(POLICY_PATH), load_manifest(), load_registry()
    registry = json.loads(json.dumps(registry))
    scoped = json.loads(json.dumps(registry["agents"]["codex"]))
    fixture_storage = Path(tempfile.gettempdir()).resolve() / "deepseek-workspace-guard-fixture"
    scoped.update(id="deepseek-harness-workspace", aliases=[], role="fixture_maintainer",
                  capabilities={"inherit_role": True, "allow": []},
                  storage={"boundary": "external", "data_root": str(fixture_storage / "data"),
                           "cache_root": str(fixture_storage / "cache")},
                  path_scopes=["packages/ai-workbench/**", "packages/ai-workbench/src/ai_workbench/e_diary/**",
                               "packages/character-system/**"])
    registry["agents"]["deepseek-harness-workspace"] = scoped
    policy = json.loads(json.dumps(policy))
    policy.setdefault("roles", {})["fixture_maintainer"] = {
        "capabilities": ["read", "invoke", "source_write"]
    }
    manifest = json.loads(json.dumps(manifest))
    if not any(item.get("id") == "ai-workbench" for item in manifest["packages"]):
        manifest["packages"].append({"id": "ai-workbench", "source_path": "packages/ai-workbench"})
    manifest["skills"] = [item for item in manifest["skills"] if item.get("id") not in {"ai-workbench-maintainer", "style-doctor"}]
    manifest["skills"] += [
        {"id": "ai-workbench-maintainer", "package_id": "ai-workbench", "role": "maintenance",
         "discovery_mode": "guarded_agent_only", "guarded_agents": ["codex", "deepseek-harness-workspace"],
         "execution_modes": {"allowed": ["text_only", "source_patch"]}},
        {"id": "style-doctor", "role": "diagnosis", "execution_modes": {"allowed": ["text_only", "record_write"]}},
    ]
    def check(path):
        return check_access(policy, manifest, registry=registry, agent_name="deepseek-harness-workspace",
                            operation="write", raw_path=path, branch="dev")["status"]
    assert check("packages/ai-workbench/src/ai_workbench/e_diary/app.py") == "ALLOW"
    assert check("packages/character-system/engineering/maintenance/character-maintainer/SKILL.md") == "ALLOW"
    assert check("packages/ai-workbench/AGENTS.md") == "DENY"
    assert check("PROJECT_CONTEXT/memory/decisions.md") == "DENY"
    assert check("shared/governance/agent_registry.yaml") == "DENY"
    workbench_skill = check_access(policy, manifest, registry=registry, agent_name="deepseek-harness-workspace",
        operation="write", raw_path="packages/ai-workbench/src/ai_workbench/e_diary/app.py",
        acting_skill="ai-workbench-maintainer", branch="dev")
    assert workbench_skill["status"] == "ALLOW"
    wrong_package = check_access(policy, manifest, registry=registry, agent_name="deepseek-harness-workspace",
        operation="write", raw_path="packages/character-system/engineering/maintenance/character-maintainer/SKILL.md",
        acting_skill="ai-workbench-maintainer", branch="dev")
    assert wrong_package["status"] == "DENY"
    foreign_registry = json.loads(json.dumps(registry))
    foreign_registry["agents"]["codex"]["id"] = "fixture-agent"
    foreign_registry["agents"]["fixture-agent"] = foreign_registry["agents"].pop("codex")
    foreign_registry["agents"]["fixture-agent"]["aliases"] = []
    foreign = check_access(policy, manifest, registry=foreign_registry, agent_name="fixture-agent",
        operation="write", raw_path="packages/ai-workbench/src/ai_workbench/e_diary/app.py",
        acting_skill="ai-workbench-maintainer", branch="dev")
    assert foreign["status"] == "DENY"
    scoped_skill = check_access(policy, manifest, registry=registry, agent_name="deepseek-harness-workspace",
        operation="write", raw_path="packages/ai-workbench/src/ai_workbench/e_diary/app.py",
        acting_skill="style-doctor", branch="dev")
    assert scoped_skill["status"] == "DENY"


@pytest.mark.skipif(os.environ.get("DSH_WORKSPACE_NATIVE_TEST") != "1", reason="requires the qualified official Harness runtime")
@pytest.mark.parametrize("mode", ["answer", "blocked", "allowed", "registered", "list"])
def test_guarded_harness_reaches_synthetic_endpoint(tmp_path, monkeypatch, mode):
    from scripts.workspace import deepseek_workspace_guard as guard
    from ai_workbench.e_chatter import deepseek
    received = []
    forbidden = tmp_path / "outside-project.txt"
    forbidden.write_text("unchanged", encoding="utf-8")
    target = (tmp_path / "fake-workspace" / "packages" / "ai-workbench" / "synthetic.txt" if mode in {"registered", "list"}
              else tmp_path / "project" / "synthetic.txt" if mode == "allowed" else forbidden)
    class Endpoint(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            events = [
                ("message_start", {"message": {"id": "synthetic", "type": "message", "role": "assistant", "content": [], "model": "deepseek-flash", "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 0}}}),
                ("content_block_start", {"index": 0, "content_block": {"type": "text", "text": ""}}),
                ("content_block_delta", {"index": 0, "delta": {"type": "text_delta", "text": "synthetic workspace result"}}),
                ("content_block_stop", {"index": 0}),
                ("message_delta", {"delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 5}}),
                ("message_stop", {}),
            ]
            if mode != "answer" and len(received) == 1:
                events[1:4] = [
                    ("content_block_start", {"index": 0, "content_block": {"type": "tool_use", "id": "fixture-tool", "name": "workspace_list" if mode == "list" else "write", "input": {}}}),
                    ("content_block_delta", {"index": 0, "delta": {"type": "input_json_delta", "partial_json": json.dumps({"path": str(target.parent)} if mode == "list" else {"file_path": str(target), "content": "modified"})}}),
                    ("content_block_stop", {"index": 0}),
                ]
                events[-2][1]["delta"]["stop_reason"] = "tool_use"
            for kind, data in events:
                self.wfile.write(("event: " + kind + "\ndata: " + json.dumps({"type": kind, **data}) + "\n\n").encode())
                self.wfile.flush()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Endpoint)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    original = guard.yaml.safe_dump
    def composition(value, **kwargs):
        for row in value:
            if row.get("id") == "llm-deepseek" and "config" in row:
                row["config"]["baseURL"] = f"http://127.0.0.1:{server.server_port}"
        return original(value, **kwargs)
    monkeypatch.setattr(guard.yaml, "safe_dump", composition)
    monkeypatch.setattr(guard, "validate_launch", lambda project, *_: Path(project))
    root = Path(__file__).resolve().parents[3]
    project = tmp_path / "project"
    project.mkdir()
    if mode in {"registered", "list"}:
        import yaml
        source = root
        root = tmp_path / "fake-workspace"
        for name in ("scripts/workspace", "shared/governance", "PROJECT_CONTEXT/tasks/registry"):
            shutil.copytree(source / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (root / "scripts/platform").mkdir(parents=True)
        shutil.copy2(source / "scripts/__init__.py", root / "scripts/__init__.py")
        shutil.copy2(source / "scripts/platform/deepseek-workspace-bridge.mjs", root / "scripts/platform/deepseek-workspace-bridge.mjs")
        manifest = json.loads((source / "workspace_manifest.yaml").read_text(encoding="utf-8"))
        manifest["workspace"]["source_of_truth"] = str(root)
        manifest.pop("skill_catalogs", None)
        manifest["skills"] = []
        (root / "workspace_manifest.yaml").write_text(json.dumps(manifest), encoding="utf-8")
        registry_path = root / "shared/governance/agent_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        scoped = registry["agents"]["deepseek-harness"].copy()
        scoped["id"] = "deepseek-harness-workspace"
        scoped["aliases"] = []
        scoped["capabilities"] = {"inherit_role": True, "allow": ["source_write"]}
        scoped["path_scopes"] = ["packages/ai-workbench/**"]
        registry["agents"]["deepseek-harness-workspace"] = scoped
        registry_path.write_text(original(registry), encoding="utf-8")
        record = {"schema_version": "1.4", "task_id": "TASK-20261107-008", "task_type": "ai_workbench_development",
                  "started_at": "2026-11-07T15:00:00Z", "status": "in_progress", "registration": {"operations": ["workspace_write"]},
                  "validation": {"status": "not_run"}, "human_edit_rounds": 0, "tokens": {}, "usability": {"status": "unknown"},
                  "owner": {"kind": "workspace_session", "agent": "deepseek-harness-workspace", "session_id": "synthetic-session", "bindings": []},
                  "git_baseline": {"branch": "dev", "head_commit": "fixture", "captured_at": "2026-11-07T15:00:00Z", "paths": []}}
        record_path = root / "PROJECT_CONTEXT/tasks/records/2026/11/07/TASK-20261107-008.json"
        record_path.parent.mkdir(parents=True)
        record_path.write_text(json.dumps(record), encoding="utf-8")
        project = target.parent
        project.mkdir(parents=True)
        if mode == "list":
            (project / "src").mkdir()
            (project / "node_modules").mkdir()
        for name in ("AGENTS.md", "packages/ai-workbench/AGENTS.md", "packages/ai-workbench/README.md", "packages/ai-workbench/shared/maintenance.md"):
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("Synthetic fixture context.\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "dev", str(root)], check=True)
        monkeypatch.setattr(guard, "__file__", str(root / "scripts/workspace/deepseek_workspace_guard.py"))
    if mode == "allowed":
        fake_guard = tmp_path / "fixture_guard.py"
        fake_guard.write_text("import json,sys\nx=json.load(sys.stdin)\nok=x.get('name')=='write' and x.get('arguments',{}).get('file_path')==" + repr(str(target)) + "\nprint(json.dumps({'allowed':ok,'reason':None if ok else 'fixture denied'}))\n", encoding="utf-8")
        monkeypatch.setattr(guard, "__file__", str(fake_guard))
    credentials = tmp_path / "credentials"
    credentials.mkdir()
    adapter = deepseek.DeepSeek(credentials, auth="api_key")
    try:
        adapter.authenticate("save_key", key="synthetic-fixture-not-a-real-key")
        models = adapter.account()["models"]
        adapter.close()
        result = guard.run_workspace(project, root, "TASK-20261107-008", "synthetic-session", None,
                                     credentials, "api_key", models[0]["id"], "synthetic request", tmp_path)
        assert "synthetic workspace result" in result
        assert len(received) >= 1
        if mode != "answer":
            assert len(received) >= 2
            assert forbidden.read_text(encoding="utf-8") == "unchanged"
            if mode == "list":
                assert "src" in json.dumps(received[1])
                assert "node_modules" not in json.dumps(received[1])
            elif mode == "blocked":
                assert "outside" in json.dumps(received[1]).lower() or "denied" in json.dumps(received[1]).lower()
            else:
                assert target.read_text(encoding="utf-8") == "modified"
    finally:
        adapter.close()
        server.shutdown()
        server.server_close()
