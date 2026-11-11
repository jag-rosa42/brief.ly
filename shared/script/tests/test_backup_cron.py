from pathlib import Path
import contextlib
import io
import subprocess
import sys
import unittest
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
import install_backup_cron as scheduler


class BackupCronTests(unittest.TestCase):
    def test_four_digit_24_hour_times(self):
        self.assertEqual(scheduler.parse_time("1234"), (12, 34))
        self.assertEqual(scheduler.parse_time("2305"), (23, 5))
        self.assertEqual(scheduler.parse_time("0203"), (2, 3))
        self.assertEqual(scheduler.parse_time("0000"), (0, 0))

    def test_invalid_times_fail_before_changing_crontab(self):
        for value in ("12h34", "2:03", "2400", "1260", "203", "12ab", "１２３４"):
            with self.subTest(value=value), mock.patch.object(scheduler, "backup_dir") as backup_dir:
                with self.assertRaisesRegex(ValueError, "BACKUP_TIME"):
                    scheduler.install(value)
                backup_dir.assert_not_called()

    def test_time_becomes_cron_minute_then_hour(self):
        with mock.patch.object(scheduler.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"):
            line = scheduler.cron_line(Path("/private/tmp/backups"), "1234")
        self.assertTrue(line.startswith("34 12 * * * "))
        self.assertIn(" backup >> ", line)

    def test_install_replaces_only_its_entry_when_time_changes(self):
        state = {"crontab": "0 1 * * * echo unrelated\n0 2 * * * echo old # ft_transcendance backup\n",
                 "writes": 0}

        def fake_run(argv, **kwargs):
            if argv[-1] == "-l":
                return subprocess.CompletedProcess(argv, 0, state["crontab"], "")
            state["crontab"] = kwargs["input"]
            state["writes"] += 1
            return subprocess.CompletedProcess(argv, 0, "", "")

        with mock.patch.object(scheduler, "backup_dir", return_value=Path("/private/tmp/backups")), \
             mock.patch.object(scheduler, "password_file"), \
             mock.patch.object(scheduler.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"), \
             mock.patch.object(scheduler.subprocess, "run", side_effect=fake_run), \
             contextlib.redirect_stdout(io.StringIO()):
            scheduler.install("2305")
            scheduler.install("2305")

        self.assertIn("0 1 * * * echo unrelated", state["crontab"])
        self.assertIn("5 23 * * * ", state["crontab"])
        self.assertEqual(state["crontab"].count(scheduler.MARKER), 1)
        self.assertEqual(state["writes"], 1)


if __name__ == "__main__":
    unittest.main()
