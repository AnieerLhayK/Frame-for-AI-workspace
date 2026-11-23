"""Bounded UTF-8 file logs shared by independent Windows/Unix processes.

This stdlib-only module is also deployed beside the installed WPS vendor source.
No process keeps a log handle open between writes: rotation and readers use the
same sidecar lock, so Windows renames cannot race another managed writer.
"""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 2


def routing_events_path(workspace_root: Path | None = None) -> Path:
    staging = os.environ.get("AI_TOOL_STAGING_DIR")
    if staging:
        return Path(staging) / "routing_events.ndjson"
    root = workspace_root or Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "workspace_manifest.yaml").read_text(encoding="utf-8-sig"))
    declared = manifest.get("runtime_roots", {}).get("workspace_logs")
    if not declared or "${" in declared or not Path(declared).is_absolute():
        raise ValueError("Declare runtime_roots.workspace_logs or set AI_TOOL_STAGING_DIR")
    return Path(declared) / "routing_events.ndjson"


@contextmanager
def file_lock(path: Path, *, timeout: float = 5.0) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Log lock unavailable: {path}")
                time.sleep(0.01)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class BoundedLog:
    def __init__(self, path: Path, *, max_bytes: int = MAX_BYTES, backups: int = BACKUP_COUNT):
        if max_bytes < 1 or backups < 0:
            raise ValueError("Invalid log retention limits")
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backups = backups

    @property
    def lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

    def volumes(self) -> list[Path]:
        return [self.path.with_name(f"{self.path.name}.{i}") for i in range(self.backups, 0, -1)] + [self.path]

    def append(self, text: str) -> None:
        payload = (text.rstrip("\n") + "\n").encode("utf-8")
        if len(payload) > self.max_bytes:
            raise ValueError("One log record exceeds the volume limit")
        with file_lock(self.lock_path):
            size = self.path.stat().st_size if self.path.exists() else 0
            if size + len(payload) > self.max_bytes:
                for index in range(self.backups, 0, -1):
                    target = self.path.with_name(f"{self.path.name}.{index}")
                    source = self.path if index == 1 else self.path.with_name(f"{self.path.name}.{index - 1}")
                    if source.exists():
                        os.replace(source, target)
                if not self.backups:
                    self.path.unlink(missing_ok=True)
            with self.path.open("ab") as handle:
                handle.write(payload)

    def read_texts(self) -> list[str]:
        with file_lock(self.lock_path):
            return [path.read_text(encoding="utf-8") for path in self.volumes() if path.is_file()]


class BoundedFileHandler(logging.Handler):
    def __init__(self, path: Path):
        super().__init__()
        self.log = BoundedLog(path)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.log.append(self.format(record))
        except (OSError, ValueError):
            self.handleError(record)
