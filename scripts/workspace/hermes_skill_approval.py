"""Host-owned policy and adapter for Hermes' native private-skill pending writes.

Vendor files stay untouched. The adapter wraps the native stage/apply seams;
only the native human slash-command handler can enter the apply context.
"""
from __future__ import annotations

import contextvars
import hashlib
import hmac
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

from scripts.workspace.manifest_loader import load_manifest as _load_manifest
from scripts.workspace.runtime import WORKSPACE_ROOT

PLUGIN_ID = "workspace-skill-approval"
REVIEW_KEY = "workspace_review"
POLICY_CONTEXT = (
    "[Owner skill policy] Workspace-registered skills and their projections are read-only. "
    "For an unregistered Hermes-created private skill, briefly suggest a change only when it "
    "has clear reusable value. Wait for the user's agreement to prepare it, then use skill_manage "
    "to stage the exact change. It is NOT saved until the HUMAN reviews /skills diff <id> and "
    "uses /skills approve <id>. Never approve your own changes, use bulk approval, disable the "
    "gate, or use terminal/file/code tools to bypass it. Background reviews must never prepare "
    "or change skills, even during memory review. Keep existing memory behavior. Do not propose "
    "a skill after every task. A correction or a successful task is not permission to save one."
)
_human_approval: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "workspace_human_skill_approval", default=None
)
_adapter_lock = threading.RLock()
_mutation_receipt: contextvars.ContextVar[str | None] = contextvars.ContextVar("workspace_skill_receipt", default=None)


def load_manifest() -> dict:
    return _load_manifest(WORKSPACE_ROOT / "workspace_manifest.yaml")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def within(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def operation(payload: dict) -> dict:
    """Normalize the current operations schema and the legacy flat Python API."""
    if payload.get("operations") is None:
        return payload
    operations = payload["operations"]
    if not isinstance(operations, list) or len(operations) != 1 or not isinstance(operations[0], dict):
        raise PermissionError("Submit exactly one skill operation per review; bulk operations are disabled")
    item = dict(operations[0])
    item.setdefault("name", payload.get("name"))
    if item.get("operations") is not None:
        raise PermissionError("Nested skill batches are disabled")
    return item


def restore_package(destination: Path, image: dict, directories: list[Path], existed: bool) -> list[str]:
    """Restore in place: a locked original file must not prevent other recovery."""
    errors: list[str] = []
    if destination.exists():
        for path in destination.rglob("*"):
            if path.is_file() and path.relative_to(destination).as_posix() not in image:
                try:
                    path.unlink()
                except OSError as error:
                    errors.append(f"remove added file {path.name}: {error}")
    if existed:
        destination.mkdir(parents=True, exist_ok=True)
        for directory in directories:
            (destination / directory).mkdir(parents=True, exist_ok=True)
        for relative, (content, stat) in image.items():
            path = destination / relative
            try:
                if path.is_file() and path.read_bytes() == content:
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                os.chmod(path, stat.st_mode)
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            except OSError as error:
                errors.append(f"restore {relative}: {error}")
    if destination.exists():
        original_dirs = {str(p) for p in directories}
        for path in sorted(destination.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir() and str(path.relative_to(destination)) not in original_dirs:
                try:
                    path.rmdir()
                except OSError:
                    pass  # Never remove a non-empty directory recursively.
        if not existed:
            try:
                destination.rmdir()
            except OSError as error:
                errors.append(f"remove added skill directory: {error}")
    return errors


class SkillPolicy:
    def __init__(self, home: Path, manifest: dict | None = None):
        self.home = home.resolve()
        self.root = self.home / "skills"
        self.manifest = manifest if manifest is not None else load_manifest()

    def registered_names(self) -> set[str]:
        result: set[str] = set()
        for item in self.manifest.get("skills", []):
            for field in ("id", "name"):
                if item.get(field):
                    result.add(str(item[field]).casefold())
            if item.get("source_path"):
                result.add(Path(item["source_path"]).name.casefold())
        return result

    def _safe_components(self, path: Path) -> None:
        # Check lexical components before resolving so a junction cannot hide.
        if not path.absolute().is_relative_to(self.root.absolute()):
            raise PermissionError("Skill target must stay inside the Hermes skills directory")
        p = path
        while True:
            if is_link(p):
                raise PermissionError("Skill maintenance cannot follow a link or junction")
            if p == self.root:
                break
            p = p.parent
        if not within(path, self.root) or within(path, WORKSPACE_ROOT):
            raise PermissionError("Workspace skill source and projections are read-only")

    def target(self, payload: dict) -> Path:
        payload = operation(payload)
        name = str(payload.get("name") or "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*(?:/[A-Za-z0-9][A-Za-z0-9_-]*)?", name):
            raise PermissionError("Use an unambiguous private skill name or category/name")
        if name.split("/")[-1].casefold() in self.registered_names():
            raise PermissionError("Workspace-registered skill names cannot be edited or shadowed")
        action = payload.get("action")
        if action not in {"create", "edit", "patch", "delete", "write_file", "remove_file"}:
            raise PermissionError("Unknown skill mutation")
        if action == "create":
            if "/" in name:
                raise PermissionError("Create takes a bare skill name")
            category = str(payload.get("category") or "")
            if category and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", category):
                raise PermissionError("Invalid skill category")
            target = self.root / category / name if category else self.root / name
            # A bare name must not select or shadow a different existing skill.
            if self._candidates(name):
                raise PermissionError("Skill already exists; prepare an explicit edit")
        else:
            candidates = self._candidates(name)
            if len(candidates) != 1:
                raise PermissionError("Private skill is missing or ambiguous")
            target = candidates[0]
            usage_path = self.root / ".usage.json"
            usage = json.loads(usage_path.read_text(encoding="utf-8-sig"))
            state = json.loads(control_path(self.home).read_text(encoding="utf-8"))
            bundled = self.root / ".bundled_manifest"
            if bundled.exists() and target.name in {line.partition(":")[0] for line in bundled.read_text(encoding="utf-8").splitlines()}:
                raise PermissionError("Bundled skills are not private Hermes-created skills")
            if (target / ".hub.json").exists() or (target / ".source.json").exists():
                raise PermissionError("Hub-installed skills retain their upstream owner")
            if (usage.get(target.name, {}).get("created_by") != "agent"
                    or target.name not in state.get("owned", [])):
                raise PermissionError("Only skills with Hermes-created provenance may be maintained")
        self._safe_components(target)
        support = payload.get("file_path")
        if support:
            if not isinstance(support, str) or "\\" in support or ":" in support:
                raise PermissionError("Invalid skill support-file path")
            file = target / support
            if not file.resolve().is_relative_to(target.resolve()):
                raise PermissionError("Support file escapes its skill")
            self._safe_components(file)
        return target

    def _candidates(self, name: str) -> list[Path]:
        if "/" in name:
            p = self.root / name
            return [p] if p.exists() or is_link(p) else []
        candidates = []
        if not self.root.exists():
            return candidates
        for entry in self.root.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.name.casefold() == name.casefold() and (entry.exists() or is_link(entry)):
                candidates.append(entry)
            if entry.is_dir() and not is_link(entry):
                candidates.extend(p for p in entry.iterdir()
                                  if p.name.casefold() == name.casefold() and (p.exists() or is_link(p)))
        return candidates

    def baseline(self, payload: dict) -> dict:
        target = self.target(payload)
        files: dict[str, str] = {}
        if target.exists():
            total = 0
            for base, directories, names in os.walk(target, followlinks=False):
                for name in directories + names:
                    p = Path(base) / name
                    self._safe_components(p)
                for name in names:
                    p = Path(base) / name
                    total += p.stat().st_size
                    if len(files) >= 512 or total > 8 * 1024 * 1024:
                        raise PermissionError("Skill package exceeds the bounded review limit")
                    files[p.relative_to(target).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        return {"target": str(target.resolve()), "exists": target.exists(), "files": files,
                "registry": digest(self.manifest)}


def control_path(home: Path) -> Path:
    return home / "state" / "workspace-skill-approval.json"


def key_path(home: Path) -> Path:
    return home / "state" / "workspace-skill-approval.key"


def source_fingerprint() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def process_birth(pid: int) -> int:
    """Bind attestation to a process lifetime, rather than a reusable PID."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            raise OSError("Cannot verify approval adapter process identity")
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                raise OSError("Cannot read approval adapter process lifetime")
            return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        finally:
            kernel.CloseHandle(handle)
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])


def signature(home: Path, value: dict) -> str:
    key = key_path(home).read_bytes()
    if len(key) != 32:
        raise PermissionError("Approval signing key is missing or invalid")
    return hmac.new(key, json.dumps(value, sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":")).encode(), hashlib.sha256).hexdigest()


def adapter_attested(home: Path, pid: int | None = None) -> bool:
    try:
        state = json.loads(control_path(home).read_text(encoding="utf-8"))
        if state.get("mode") != "approval":
            return False
        p = home / "state" / f"skill-approval-{pid or os.getppid()}.json"
        marker = json.loads(p.read_text(encoding="utf-8"))
        seal = marker.pop("signature")
        return (marker.get("pid") == (pid or os.getppid())
                and marker.get("birth") == process_birth(pid or os.getppid())
                and marker.get("source") == source_fingerprint()
                and hmac.compare_digest(seal, signature(home, marker)))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def install(ctx) -> None:
    """Install a pinned native adapter, failing closed when its seams are absent."""
    from hermes_constants import get_hermes_home
    home = Path(get_hermes_home()).resolve()
    state = json.loads(control_path(home).read_text(encoding="utf-8"))
    if state.get("mode") == "blocked":
        # The legacy shell-hook dispatcher fails open on subprocess faults.
        # Its fallback also removes write-capable toolsets; this synchronous
        # callback supplies a second boundary without native approval APIs.
        def legacy_gate(**kwargs):
            try:
                from scripts.workspace.hermes_workspace_guard import evaluate
                return evaluate({"hook_event_name": "pre_tool_call", "tool_name": kwargs.get("tool_name"),
                                 "tool_input": kwargs.get("args"), "session_id": kwargs.get("session_id"),
                                 "cwd": str(home)})
            except Exception:
                return {"action": "block", "message": "Legacy fallback guard is unavailable; tool execution denied"}
        ctx.register_hook("pre_tool_call", legacy_gate)
        ctx.register_hook("pre_llm_call", lambda **kwargs: {"context": POLICY_CONTEXT})
        return
    from tools import skill_manager_tool as manager, write_approval as wa
    from tools import skill_provenance as provenance, skill_ledger as ledger, skill_usage as usage
    from hermes_cli import write_approval_commands as commands
    from agent.skill_utils import parse_frontmatter

    if getattr(manager, "_workspace_approval_adapter", None) == source_fingerprint():
        return
    required = [(manager, "_run_write_gate"), (manager, "apply_skill_pending"),
                (manager, "_ACTION_HANDLERS"), (wa, "stage_write"),
                (commands, "handle_pending_subcommand"), (ledger, "capture_before"),
                (ledger, "append_entry"), (ledger, "record_mutation")]
    if any(not hasattr(obj, name) for obj, name in required):
        raise RuntimeError("Hermes native skill approval API changed; skill writes remain disabled")

    original_stage, original_gate = wa.stage_write, manager._run_write_gate
    original_apply = manager.apply_skill_pending
    original_commands = commands.handle_pending_subcommand
    originals = dict(manager._ACTION_HANDLERS)

    def policy() -> SkillPolicy:
        return SkillPolicy(home)

    def target(payload: dict) -> Path:
        expected = policy().target(payload)
        op = operation(payload)
        if op["action"] == "create":
            actual = manager._resolve_skill_dir(op["name"], op.get("category"))
        else:
            found = manager._find_skill(op["name"])
            if not found:
                raise PermissionError("Native skill resolver did not find the approved private skill")
            actual = found["path"]
        if Path(actual).absolute() != expected.absolute() or Path(actual).resolve() != expected.resolve():
            raise PermissionError("Native skill resolver differs from the approved private target")
        text = None
        action = op["action"]
        if action in {"create", "edit"} or (action == "patch" and op.get("content")):
            text = op.get("content")
        elif action == "write_file" and op.get("file_path") == "SKILL.md":
            text = op.get("file_content")
        elif action == "patch" and op.get("file_path") in {None, "SKILL.md"}:
            text = (expected / "SKILL.md").read_text(encoding="utf-8-sig")
            if isinstance(op.get("old_string"), str) and isinstance(op.get("new_string"), str):
                text = text.replace(op["old_string"], op["new_string"], -1 if op.get("replace_all") else 1)
        if isinstance(text, str):
            metadata, _ = parse_frontmatter(text)
            if str(metadata.get("name", "")).casefold() in policy().registered_names():
                raise PermissionError("A private skill cannot shadow a Workspace-registered display name")
        return expected

    def ensure_enabled() -> None:
        state = json.loads(control_path(home).read_text(encoding="utf-8"))
        if state.get("mode") != "approval" or not wa.write_approval_enabled(wa.SKILLS):
            raise PermissionError("Private skill approval is unavailable; no write is allowed")

    def run_gate(builder):
        ensure_enabled()
        if provenance.is_background_review():
            return json.dumps({"success": False, "error": "Background reviews cannot prepare or write skills"})
        return original_gate(builder)

    def stage(subsystem, payload, **kwargs):
        if subsystem != wa.SKILLS:
            return original_stage(subsystem, payload, **kwargs)
        with _adapter_lock:
            ensure_enabled()
            if provenance.is_background_review():
                raise PermissionError("Background skill drafts are disabled")
            review = policy().baseline(payload)
            target(payload)
            record = original_stage(subsystem, payload, **kwargs)
            record[REVIEW_KEY] = review
            record["workspace_signature"] = signature(home, record)
            atomic_json(home / "pending" / "skills" / f"{record['id']}.json", record)
            return record

    def verified_record(identifier: str, payload: dict) -> dict:
        ensure_enabled()
        record = wa.get_pending(wa.SKILLS, identifier)
        if not isinstance(record, dict):
            raise PermissionError("Pending write is missing or already applied")
        record = dict(record)
        seal = record.pop("workspace_signature", "")
        if not isinstance(seal, str) or not hmac.compare_digest(seal, signature(home, record)):
            raise PermissionError("Pending content changed or was not prepared by the approval adapter")
        if record.get("payload") != payload or record.get(REVIEW_KEY) != policy().baseline(payload):
            raise PermissionError("Skill target, registry, or baseline changed; reject and prepare a new review")
        target(payload)
        return record

    def apply(payload):
        identifier = _human_approval.get()
        if not identifier or provenance.is_background_review():
            raise PermissionError("Only a human /skills approve <id> command may apply a skill write")
        with _adapter_lock:
            verified_record(identifier, payload)
            op = operation(payload)
            token = _mutation_receipt.set(None)
            try:
                result = original_apply(op)
                if json.loads(result).get("success"):
                    try:
                        state = json.loads(control_path(home).read_text(encoding="utf-8"))
                        owned = set(state.get("owned", []))
                        if op.get("action") == "create":
                            usage.record_created(op["name"], agent_created=True)
                            owned.add(op["name"])
                        elif op.get("action") == "delete":
                            owned.discard(op["name"].split("/")[-1])
                        state["owned"] = sorted(owned)
                        atomic_json(control_path(home), state)
                    except Exception as error:
                        receipt = _mutation_receipt.get()
                        restored, note = ledger.rollback_entry(receipt) if receipt else (False, "missing receipt")
                        if restored:
                            return json.dumps({"success": False, "error": "Ownership state commit failed; skill restored using native ledger"})
                        # Revocation needs no free disk space. Without its signed
                        # marker, the independent shell guard denies skill calls.
                        (home / "state" / f"skill-approval-{os.getpid()}.json").unlink(missing_ok=True)
                        raise RuntimeError(f"Ownership state failed ({error}); recovery receipt {receipt}: {note}")
                return result
            finally:
                _mutation_receipt.reset(token)

    def handle(subsystem, args, **kwargs):
        if subsystem != wa.SKILLS:
            return original_commands(subsystem, args, **kwargs)
        verb = args[0].lower() if args else ""
        if verb in {"approval", "mode"} and len(args) > 1 and args[1].lower() not in {"on", "true", "yes", "1", "enable", "enabled"}:
            return "Owner policy requires skills.write_approval=true; change this through Codex maintenance."
        if verb not in {"approve", "apply"}:
            return original_commands(subsystem, args, **kwargs)
        if len(args) != 2 or not re.fullmatch(r"[0-9a-f]{8}", args[1]):
            return "Approve one reviewed change: /skills approve <id>. Bulk approval is disabled."
        if provenance.is_background_review():
            return "Background agents cannot approve skill changes."
        token = _human_approval.set(args[1])
        try:
            return original_commands(subsystem, args, **kwargs)
        finally:
            _human_approval.reset(token)

    def action_wrapper(action, native):
        def guarded(args):
            identifier = _human_approval.get()
            if not identifier:
                raise PermissionError("Unapproved native skill handler call")
            payload = wa.get_pending(wa.SKILLS, identifier)["payload"]
            verified_record(identifier, payload)  # Runs inside the native per-skill mutation lock.
            destination = target(payload)
            before = ledger.capture_before(destination if destination.exists() else None, skill=destination.name)
            if before is None:
                raise PermissionError("Cannot capture rollback evidence; skill was not changed")
            checkpoint = ledger.append_entry("pre-rollback", destination.name, before=before, after=before,
                                             evidence={"pending_id": identifier, "operation": action})
            if not checkpoint:
                raise PermissionError("Cannot persist rollback evidence; skill was not changed")
            # Keep a bounded in-memory restoration image until the mandatory
            # post-write ledger receipt is durable. Native telemetry alone is
            # deliberately best-effort and cannot be the rollback guarantee.
            existed = destination.exists()
            image = {p.relative_to(destination).as_posix(): (p.read_bytes(), p.stat())
                     for p in destination.rglob("*") if p.is_file()} if existed else {}
            directories = [p.relative_to(destination) for p in destination.rglob("*") if p.is_dir()] if existed else []
            try:
                result = native(args)
                success = isinstance(result, dict) and result.get("success")
                if success:
                    receipt = ledger.record_mutation(action, destination.name, before=before,
                                                     after_root=destination if destination.exists() else None,
                                                     evidence={"pending_id": identifier, "owner_approved": True})
                    if receipt:
                        _mutation_receipt.set(receipt)
                        return result
                    result = {"success": False, "error": "Post-write rollback receipt failed"}
            except Exception as error:
                result = {"success": False, "error": f"Native skill operation failed: {error}"}
            # Failure may follow a partial native delete or a failed atomic
            # write. Restore bytes and metadata before returning any failure.
            policy()._safe_components(destination)
            errors = restore_package(destination, image, directories, existed)
            if errors:
                recovery = home / "state" / f"skill-recovery-{identifier}.json"
                atomic_json(recovery, {"pending_id": identifier, "checkpoint": checkpoint,
                                       "target": str(destination), "errors": errors})
                state = json.loads(control_path(home).read_text(encoding="utf-8"))
                state["mode"] = "blocked"
                atomic_json(control_path(home), state)
                raise RuntimeError(f"Skill recovery incomplete; writes disabled. Recovery evidence: {recovery}")
            if isinstance(result, dict):
                result["error"] = result.get("error", "Skill operation failed") + "; original package restored"
            return result
        return guarded

    wa.stage_write = stage
    manager._run_write_gate = run_gate
    manager.apply_skill_pending = apply
    commands.handle_pending_subcommand = handle
    manager._ACTION_HANDLERS.update({a: action_wrapper(a, f) for a, f in originals.items()})
    manager._workspace_approval_adapter = source_fingerprint()

    def pre_tool(**kwargs):
        name = str(kwargs.get("tool_name") or "")
        if name == "skill_manage":
            try:
                ensure_enabled()
                if provenance.is_background_review():
                    raise PermissionError("Background skill drafts are disabled")
                args = kwargs.get("args") or {}
                target(args)
            except Exception as error:
                return {"action": "block", "message": str(error)}
        return None

    ctx.register_hook("pre_tool_call", pre_tool)
    ctx.register_hook("pre_llm_call", lambda **kwargs: {"context": POLICY_CONTEXT})
    marker = {"pid": os.getpid(), "birth": process_birth(os.getpid()), "source": source_fingerprint()}
    marker["signature"] = signature(home, marker)
    atomic_json(home / "state" / f"skill-approval-{os.getpid()}.json", marker)
