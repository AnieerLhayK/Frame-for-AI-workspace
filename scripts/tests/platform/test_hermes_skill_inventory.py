from __future__ import annotations
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from scripts.platform.hermes_skill_inventory import WORKER, compare_inventory, inventory


class HermesInventoryTests(unittest.TestCase):
    def test_mismatch_compares_names_not_just_counts(self):
        result = compare_inventory({"cli_enabled": ["one"], "native_enabled": ["two"]}, set())
        self.assertEqual(result["status"], "MISMATCH")
        self.assertEqual(result["only_cli"], ["one"])
        self.assertEqual(result["only_native"], ["two"])

    def test_disabled_rows_do_not_prove_enabled_registration(self):
        result = compare_inventory({"cli_all": ["one"], "cli_enabled": [], "native_enabled": []}, {"one"})
        self.assertEqual(result["missing_registered"], ["one"])
        self.assertEqual(result["status"], "MISMATCH")

    def test_matching_names_pass(self):
        self.assertEqual(compare_inventory({"cli_enabled": ["one"], "native_enabled": ["one"]}, {"one"})["status"], "PASS")

    def test_missing_runtime_stops_without_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                inventory({"runtime_roots": {"hermes": directory}, "platform_roots": {"hermes": directory + "/skills"}})

    def test_worker_rejects_file_writes_and_subprocesses(self):
        guard = WORKER.split("from unittest.mock", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "must-not-exist"
            for operation in [f"open({str(path)!r}, 'w')", "__import__('subprocess').run([sys.executable, '-c', 'pass'])"]:
                result = subprocess.run([sys.executable, "-B", "-c", guard + "\n" + operation], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("read-only inventory denied", result.stderr)
                self.assertFalse(path.exists())

    def test_null_sink_is_allowed_without_permitting_real_file_writes(self):
        guard = WORKER.split("from unittest.mock", 1)[0]
        result = subprocess.run([sys.executable, "-B", "-c", guard + "\nopen(os.devnull, 'w').write('discarded')"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_guard_covers_truncation_exec_and_network_send_events(self):
        guard = WORKER.split("from unittest.mock", 1)[0]
        for event in ["os.truncate", "os.exec", "os.posix_spawn", "socket.sendto", "socket.sendmsg", "socket.getaddrinfo", "winreg.SetValue"]:
            result = subprocess.run([sys.executable, "-B", "-c", guard + "\nsys.audit(" + repr(event) + ")"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, event)
            self.assertIn("read-only inventory denied", result.stderr, event)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.txt"
            path.write_text("unchanged", encoding="utf8")
            result = subprocess.run([sys.executable, "-B", "-c", guard + "\nos.truncate(" + repr(str(path)) + ", 0)"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_text(encoding="utf8"), "unchanged")
