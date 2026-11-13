#!/usr/bin/env python3
"""Run verified host backups periodically without cron."""

import argparse
import datetime as dt
import fcntl
import os
import signal
import subprocess
import sys
import threading
import time

from backup import ROOT, backup_dir, password_file


def report(message: str) -> None:
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    print(f"{stamp} backup scheduler: {message}", flush=True)


def run_once(log) -> bool:
    """make backup succeeds only after archive verification and status recording."""
    report("starting make backup")
    try:
        result = subprocess.run(
            ["make", "--no-print-directory", "-C", str(ROOT), "backup"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as error:
        report(f"failed to start backup: {error}")
        return False
    if result.returncode:
        report(f"backup FAILED (exit {result.returncode}); see {log.name}")
        return False
    report("backup completed and verified")
    return True


def schedule(interval: int, stopped: threading.Event, log) -> None:
    """Run immediately, skip missed slots, and never overlap our own runs."""
    deadline = time.monotonic()
    while not stopped.is_set():
        run_once(log)
        deadline += interval
        now = time.monotonic()
        if deadline <= now:
            deadline += (int((now - deadline) // interval) + 1) * interval
        stopped.wait(max(0, deadline - now))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=300,
                        help="seconds between starts (default: 300)")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    os.umask(0o077)
    destination = backup_dir()
    password_file()
    stopped = threading.Event()
    # Finish a running backup before exiting; never abandon its lock or staging files.
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stopped.set())
    with (destination / ".backup-scheduler.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another backup scheduler is already running") from error
        with (destination / "backup.log").open("a", buffering=1) as log:
            report(f"running every {args.interval}s; backup output: {log.name}")
            schedule(args.interval, stopped, log)
    report("stopped")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"backup scheduler: {error}", file=sys.stderr)
        sys.exit(1)
