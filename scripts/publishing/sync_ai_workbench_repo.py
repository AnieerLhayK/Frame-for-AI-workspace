"""Host adapter for the registered ai-workbench projection."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from scripts.publishing import registered_repo_sync as sync
from scripts.publishing.workspace_state import workspace_clean_for_record
from scripts.workspace.agent_governance import POLICY_PATH, load_yaml
from scripts.workspace.runtime import WORKSPACE_ROOT

PUBLISHER_ID = "ai_workbench"
PUBLISHER_SCRIPT = "scripts/publishing/sync_ai_workbench_repo.py"


def projection_module(source):
    spec = importlib.util.spec_from_file_location("ai_workbench_projection", source / "scripts/projection.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config(policy):
    entry = policy["managed_platform_publishers"][PUBLISHER_ID]
    contract = (WORKSPACE_ROOT / entry["contract_file"]).resolve()
    if not contract.is_relative_to(WORKSPACE_ROOT) or not contract.is_file() or contract.name != "projection-contract.json":
        raise ValueError("Invalid registered package contract")
    remotes = entry["remote_urls"]
    if not isinstance(remotes, list) or len(remotes) != 1 or not isinstance(remotes[0], str):
        raise ValueError("Publisher requires one registered remote")
    return contract.parent, Path(entry["staging_path"]), remotes[0]


def verify_baseline(path, ref, projection):
    result = sync.run_git(["git", "show", f"{ref}:PROJECTION_SOURCE.json"], path)
    if result.returncode:
        raise RuntimeError("Nonempty remote is not a recognized projection; audit required")
    try:
        marker = projection.validate_provenance(json.loads(result.stdout), require_revision=True)
        revision = marker["workspace_commit"]
        ancestry = sync.run_git(["git", "merge-base", "--is-ancestor", revision, "HEAD"], WORKSPACE_ROOT)
        if ancestry.returncode:
            raise ValueError("Unknown or unaccepted Workspace revision")
        prefix = marker["source_path"] + "/"
        contract_result = sync.run_git(["git", "show", f"{revision}:{prefix}projection-contract.json"], WORKSPACE_ROOT)
        if contract_result.returncode:
            raise ValueError("Missing authoritative contract")
        files = projection.contract_files(json.loads(contract_result.stdout))

        def tree(root, tree_ref, *paths):
            listing = sync.run_git(["git", "ls-tree", "-r", "-z", tree_ref, "--", *paths], root)
            if listing.returncode:
                raise ValueError("Cannot inspect projection tree")
            entries = {}
            for entry in listing.stdout.split("\0"):
                if not entry:
                    continue
                metadata, name = entry.split("\t", 1)
                mode, kind, digest = metadata.split()
                if kind != "blob" or mode not in {"100644", "100755"}:
                    raise ValueError("Nonregular projection entry")
                entries[name] = digest
            return entries

        authoritative = tree(WORKSPACE_ROOT, revision, marker["source_path"])
        expected = {name: authoritative[prefix + name] for name in files}
        payload = (json.dumps(marker, indent=2) + "\n").encode("utf-8")
        expected["PROJECTION_SOURCE.json"] = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
        if tree(path, ref) != expected:
            raise ValueError("Remote payload differs from its authoritative export")
    except (ValueError, TypeError, KeyError) as error:
        raise RuntimeError("Nonempty remote failed authoritative baseline verification; audit required") from error


def verify_export(staging, source, revision, *, run_tests=True, temporary_root=None):
    projection = projection_module(source)
    projection.check(staging, revision, require_revision=True, expected_files=projection.allowed_files(source) + projection.GENERATED)
    if not run_tests:
        return
    # Leave source/public inventory untouched, including bytecode and pytest caches.
    environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="ai-workbench-tests-", dir=temporary_root or staging.parent) as temporary:
        commands = (
            [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(Path(temporary) / "pytest"), "tests"],
            [sys.executable, "-B", "-c", "import sys; sys.path.insert(0, 'src'); from ai_workbench.app import create_application, Workbench; from PySide6.QtCore import QTimer; a=create_application(); w=Workbench(demo=True); w.show(); QTimer.singleShot(300, a.quit); raise SystemExit(a.exec())"],
        )
        for command in commands:
            result = subprocess.run(command, cwd=staging, env=environment, text=True, capture_output=True, timeout=180)
            print((result.stdout + result.stderr).strip())
            if result.returncode:
                raise RuntimeError("Independent simulated verification failed")
    projection.check(staging, revision, require_revision=True, expected_files=projection.allowed_files(source) + projection.GENERATED)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--agent", default="codex")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--push", action="store_true")
    mode.add_argument("--preview", action="store_true")
    parser.add_argument("--force-dirty", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args(argv)
    if args.force_dirty and not args.preview:
        parser.error("--force-dirty is only valid for preview")
    completed = False
    try:
        source, staging, remote = config(load_yaml(POLICY_PATH))
        sync.require_managed_publish_authorization(publisher_id=PUBLISHER_ID, publisher_script=PUBLISHER_SCRIPT,
            record_id=args.record_id, agent=args.agent, staging_path=str(staging), remote_url=remote)
        if not args.force_dirty and not workspace_clean_for_record(WORKSPACE_ROOT, args.record_id):
            raise RuntimeError("Workspace must be clean before synchronization")
        result = sync.run_git(["git", "rev-parse", "HEAD"], WORKSPACE_ROOT)
        if result.returncode:
            raise RuntimeError("Cannot resolve Workspace revision")
        revision = result.stdout.strip()
        projection = projection_module(source)
        projection.validate_provenance(projection.provenance(revision), require_revision=True)
        if staging.exists() and any(item.name != "checkout" for item in staging.iterdir()):
            raise RuntimeError("Registered staging has unexpected contents; audit required")
        checkout = staging / "checkout"
        sync.prepare_initializable_staging(checkout, remote, lambda path, ref: verify_baseline(path, ref, projection))
        projection.export(source, checkout, source_revision=revision, git_staging=True)
        verify_export(checkout, source, revision, run_tests=not args.skip_tests)
        if args.preview:
            sync.preview_staging_remotely(checkout, "preview: ai-workbench portable tools")
        elif args.push:
            sync.commit_and_push(checkout, "sync: ai-workbench portable tools")
            result = sync.run_git(["git", "rev-parse", "HEAD"], checkout)
            print(f"[OK] Workspace {revision}; projection {result.stdout.strip()}")
        else:
            print(f"[OK] Dry run verified Workspace {revision}; no remote changes")
        completed = True
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    finally:
        if completed:
            cleaned = sync.cleanup_staging(staging, staging)
            print(f"[INFO] Registered staging cleanup: {'complete' if cleaned else 'retained'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
