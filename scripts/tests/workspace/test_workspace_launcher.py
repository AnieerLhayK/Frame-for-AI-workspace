from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.workspace_launcher import (
    MARKER,
    inspect_launcher,
    install_launcher,
    launcher_content,
    uninstall_launcher,
)


class WorkspaceLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.install_dir = Path(self.temp_dir.name) / "bin"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_launcher_quotes_cli_path_and_forwards_arguments(self) -> None:
        text = launcher_content(Path(r"D:\A Folder\workspace_cli.py"))
        self.assertIn('"D:\\A Folder\\workspace_cli.py" %*', text)
        self.assertIn(MARKER, text)
        self.assertIn("exit /b !errorlevel!", text)

    def test_install_and_uninstall_managed_launcher(self) -> None:
        with patch("scripts.workspace_launcher.path_entries", return_value=set()):
            installed = install_launcher(self.install_dir)
            self.assertEqual(installed["status"], "INSTALLED")
            self.assertTrue(inspect_launcher(self.install_dir)["current"])

            removed = uninstall_launcher(self.install_dir)
            self.assertEqual(removed["status"], "UNINSTALLED")
            self.assertFalse((self.install_dir / "workspace.cmd").exists())

    def test_unmanaged_launcher_is_not_replaced_or_removed(self) -> None:
        self.install_dir.mkdir(parents=True)
        launcher = self.install_dir / "workspace.cmd"
        launcher.write_text("@echo off\necho other\n", encoding="utf-8")
        self.assertEqual(install_launcher(self.install_dir)["status"], "BLOCKED")
        self.assertEqual(uninstall_launcher(self.install_dir)["status"], "BLOCKED")
        self.assertIn("echo other", launcher.read_text(encoding="utf-8"))

    def test_dry_run_does_not_create_launcher(self) -> None:
        result = install_launcher(self.install_dir, dry_run=True)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertFalse((self.install_dir / "workspace.cmd").exists())

    def test_active_windows_launcher_schedules_self_removal(self) -> None:
        install_launcher(self.install_dir)
        with (
            patch("scripts.workspace_launcher.os.name", "nt"),
            patch.dict(
                "scripts.workspace_launcher.os.environ",
                {
                    "WORKSPACE_LAUNCHER_PATH": str(
                        self.install_dir / "workspace.cmd"
                    )
                },
                clear=False,
            ),
            patch("scripts.workspace_launcher.schedule_delete") as schedule,
        ):
            result = uninstall_launcher(self.install_dir)
        self.assertEqual(result["status"], "UNINSTALL_SCHEDULED")
        schedule.assert_called_once_with(self.install_dir / "workspace.cmd")

    def test_inspection_distinguishes_unmanaged_launcher(self) -> None:
        self.install_dir.mkdir(parents=True)
        launcher = self.install_dir / "workspace.cmd"
        launcher.write_text("@echo off\necho unmanaged\n", encoding="utf-8")
        status = inspect_launcher(self.install_dir)
        self.assertTrue(status["exists"])
        self.assertFalse(status["managed"])


if __name__ == "__main__":
    unittest.main()
