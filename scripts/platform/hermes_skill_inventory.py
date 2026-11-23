"""Compare Hermes discovery in one fixed read-only process, without CLI bootstrap."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

WORKER = r'''import sys, os, json
blocked_events = []

def deny_mutation(event, args):
    if event == "open":
        if isinstance(args[0], str) and args[0].casefold() == os.devnull.casefold():
            return  # Vendor logging may discard output; this does not mutate a file.
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            blocked_events.append(event)
            raise PermissionError("read-only inventory denied file write")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.chmod", "os.utime", "os.system", "os.link", "os.symlink", "subprocess.Popen", "socket.connect", "socket.bind",
                "os.truncate", "os.exec", "os.posix_spawn", "os.fork", "os.spawn", "os.startfile",
                "os.chown", "os.chflags", "os.setxattr", "os.removexattr", "os.mknod",
                "shutil.copyfile", "shutil.copytree", "shutil.move", "shutil.rmtree",
                "socket.sendto", "socket.sendmsg", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
                "winreg.CreateKey", "winreg.DeleteKey", "winreg.DeleteValue", "winreg.SetValue", "winreg.SaveKey", "winreg.LoadKey"}:
        blocked_events.append(event)
        raise PermissionError("read-only inventory denied " + event)
sys.addaudithook(deny_mutation)
# CPython's platform probe otherwise shells out to `ver` on Windows. Keep
# this diagnostic process entirely within the already available OS API.
import platform
if sys.platform == "win32":
    def windows_version(system="", release="", version="", *args, **kwargs):
        value = sys.getwindowsversion()
        return system or "Windows", release or str(value.major), f"{value.major}.{value.minor}.{value.build}"
    platform._syscmd_ver = windows_version
from unittest.mock import patch
from tools.skills_tool import _find_all_skills, SKILLS_DIR
from hermes_cli.skills_hub import do_list
import tools.skills_hub as hub

def existing_hub():
    for p in [hub.QUARANTINE_DIR, hub.INDEX_CACHE_DIR, hub.LOCK_FILE, hub.AUDIT_LOG, hub.TAPS_FILE]:
        if not p.exists(): raise FileNotFoundError("inventory requires existing hub metadata: " + str(p))

class Capture:
    def __init__(self): self.names = []; self.enabled = []
    def print(self, obj):
        if hasattr(obj, "columns"):
            self.names.extend(obj.columns[0]._cells)
            self.enabled.extend(name for name, state in zip(obj.columns[0]._cells, obj.columns[4]._cells) if "enabled" in state)

capture = Capture()
with patch.object(hub, "ensure_hub_dirs", existing_hub):
    do_list(console=capture)
native = sorted(s["name"] for s in _find_all_skills())
if blocked_events:
    raise PermissionError("read-only inventory blocked operations: " + ", ".join(blocked_events))
print(json.dumps({"home": os.environ["HERMES_HOME"], "platform": os.environ["HERMES_SESSION_PLATFORM"], "skills_root": str(SKILLS_DIR.resolve()), "cli_all": sorted(capture.names), "cli_enabled": sorted(capture.enabled), "native_enabled": native}))
'''


def compare_inventory(data: dict, expected: set[str]) -> dict:
    cli, native = set(data["cli_enabled"]), set(data["native_enabled"])
    missing = sorted(expected - (cli & native))
    return {**data, "status": "PASS" if cli == native and not missing else "MISMATCH",
            "only_cli": sorted(cli - native), "only_native": sorted(native - cli),
            "missing_registered": missing, "cli_count": len(cli), "native_count": len(native)}


def inventory(manifest: dict) -> dict:
    declared = manifest.get("runtime_roots", {}).get("hermes")
    skills = manifest.get("platform_roots", {}).get("hermes")
    if not isinstance(declared, str) or not declared or not isinstance(skills, str) or not skills:
        raise ValueError("Declare runtime_roots.hermes and platform_roots.hermes before inventory")
    installation = Path(declared)
    python = installation / "venv/Scripts/python.exe"
    home = Path(skills).parent
    if not python.is_file():
        raise FileNotFoundError(f"Hermes Python not installed: {python}")
    env = {**os.environ, "HERMES_HOME": str(home), "HERMES_SESSION_PLATFORM": "cli", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("PYTHONPATH", None)
    result = subprocess.run([str(python), "-B", "-c", WORKER], cwd=installation,
                            env=env, text=True, encoding="utf8", capture_output=True, check=True, timeout=30)
    expected = {str(p["id"]).split(".", 1)[1] for p in manifest.get("projections", []) if p.get("platform") == "hermes" and p.get("kind", "skill") == "skill"}
    data = compare_inventory(json.loads(result.stdout), expected)
    data["implementation_sha256"] = {name: hashlib.sha256((installation / name).read_bytes()).hexdigest() for name in ["hermes_cli/skills_hub.py", "tools/skills_tool.py"]}
    return data


def main() -> int:
    from scripts.workspace.manifest_loader import load_manifest
    root = Path(__file__).resolve().parents[2]
    try:
        data = inventory(load_manifest(root / "workspace_manifest.yaml"))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.strip().splitlines()[-1] if exc.stderr and exc.stderr.strip() else f"Inventory subprocess failed: {exc.returncode}"
        elif isinstance(exc, subprocess.TimeoutExpired):
            detail = "Inventory subprocess exceeded its 30-second budget"
        print(json.dumps({"status": "ERROR", "error": detail}, ensure_ascii=True))
        return 1
    print(json.dumps(data, ensure_ascii=True, indent=2))
    return 0 if data["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
