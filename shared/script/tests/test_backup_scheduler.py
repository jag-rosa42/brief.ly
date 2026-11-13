from pathlib import Path
import io
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backup_scheduler as scheduler


class BackupSchedulerTests(unittest.TestCase):
    def test_backup_command_and_failure_reporting(self):
        log = mock.Mock(name="log")
        for code in (0, 2):
            with self.subTest(code=code), mock.patch.object(
                scheduler.subprocess, "run",
                return_value=subprocess.CompletedProcess([], code),
            ) as run, mock.patch.object(scheduler, "report") as report:
                self.assertEqual(scheduler.run_once(log), code == 0)
                self.assertEqual(run.call_args.args[0],
                                 ["make", "--no-print-directory", "-C", str(scheduler.ROOT), "backup"])
                self.assertIs(run.call_args.kwargs["stdout"], log)
                self.assertIn("FAILED" if code else "verified", report.call_args.args[0])

    def test_missing_make_is_reported_as_failure(self):
        with mock.patch.object(scheduler.subprocess, "run", side_effect=FileNotFoundError), \
             mock.patch.object(scheduler, "report"):
            self.assertFalse(scheduler.run_once(io.StringIO()))

    def test_failure_does_not_stop_next_run(self):
        stopped = mock.Mock()
        stopped.is_set.side_effect = [False, False, True]
        with mock.patch.object(scheduler, "run_once", side_effect=[False, True]) as run, \
             mock.patch.object(scheduler.time, "monotonic", side_effect=[0, 10, 310]):
            scheduler.schedule(300, stopped, io.StringIO())
        self.assertEqual(run.call_count, 2)
        self.assertEqual(stopped.wait.call_args_list, [mock.call(290), mock.call(290)])

    def test_slow_run_skips_missed_slots(self):
        stopped = mock.Mock()
        stopped.is_set.side_effect = [False, True]
        with mock.patch.object(scheduler, "run_once"), \
             mock.patch.object(scheduler.time, "monotonic", side_effect=[0, 650]):
            scheduler.schedule(300, stopped, io.StringIO())
        stopped.wait.assert_called_once_with(250)

    def test_stopped_scheduler_does_not_run(self):
        stopped = mock.Mock()
        stopped.is_set.return_value = True
        with mock.patch.object(scheduler, "run_once") as run:
            scheduler.schedule(300, stopped, io.StringIO())
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
