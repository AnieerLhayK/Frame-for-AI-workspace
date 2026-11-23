from __future__ import annotations

import json
import logging
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.workspace.runtime_logging import BoundedFileHandler, BoundedLog, routing_events_path


def write_records(path: str, worker: int, count: int, limit: int) -> None:
    log = BoundedLog(Path(path), max_bytes=limit)
    for index in range(count):
        log.append(json.dumps({"worker": worker, "index": index, "payload": "中" * 12}))


class RuntimeLoggingTests(unittest.TestCase):
    def test_concurrent_processes_retain_complete_records_across_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.ndjson"
            # Cross the first volume, but retain all records in three volumes.
            workers = [multiprocessing.get_context("spawn").Process(target=write_records, args=(str(path), i, 30, 10000)) for i in range(4)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(30)
                self.assertFalse(worker.is_alive())
                self.assertEqual(worker.exitcode, 0)
            log = BoundedLog(path, max_bytes=10000)
            events = [json.loads(line) for text in log.read_texts() for line in text.splitlines()]
            self.assertEqual({(x["worker"], x["index"]) for x in events}, {(i, j) for i in range(4) for j in range(30)})
            self.assertTrue(path.with_name(path.name + ".1").exists())

    def test_capacity_and_retained_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = BoundedLog(Path(tmp) / "events.ndjson", max_bytes=100)
            for index in range(40):
                log.append(json.dumps({"index": index, "text": "x" * 20}))
            volumes = [p for p in log.volumes() if p.exists()]
            self.assertEqual(len(volumes), 3)
            self.assertTrue(all(p.stat().st_size <= 100 for p in volumes))
            records = [json.loads(line)["index"] for text in log.read_texts() for line in text.splitlines()]
            self.assertEqual(records, sorted(records))
            self.assertEqual(records[-1], 39)
            before = [p.read_bytes() for p in volumes]
            with self.assertRaises(ValueError):
                log.append("x" * 101)
            self.assertEqual(before, [p.read_bytes() for p in volumes])

    def test_manifest_and_staging_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace_manifest.yaml").write_text(json.dumps({"runtime_roots": {"workspace_logs": str(root / "logs")}}))
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(routing_events_path(root), root / "logs/routing_events.ndjson")
            with patch.dict(os.environ, {"AI_TOOL_STAGING_DIR": str(root / "override")}):
                self.assertEqual(routing_events_path(root), root / "override/routing_events.ndjson")
            (root / "workspace_manifest.yaml").write_text("{}")
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                routing_events_path(root)

    def test_handler_failure_does_not_escape_and_resolver_remains_best_effort(self):
        handler = BoundedFileHandler(Path("unused"))
        with patch.object(handler.log, "append", side_effect=PermissionError), patch.object(handler, "handleError") as report:
            handler.emit(logging.makeLogRecord({"msg": "hello"}))
            report.assert_called_once()
        from scripts.workspace.resolve_task_context import record_routing_event
        with patch("scripts.workspace.runtime_logging.BoundedLog.append", side_effect=PermissionError):
            record_routing_event({})
