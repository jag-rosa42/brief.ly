#!/usr/bin/env python3
"""Install the host's daily cron entry for the normal backup command."""

import argparse
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from backup import ROOT, backup_dir, password_file


MARKER = "# ft_transcendance backup"


def parse_time(value: str) -> tuple[int, int]:
    """Convert four 24-hour digits, HHMM, into cron's hour and minute."""
    if len(value) != 4 or not value.isascii() or not value.isdigit():
        raise ValueError("BACKUP_TIME must be four digits in 24-hour HHMM format")
    hour, minute = int(value[:2]), int(value[2:])
    if hour > 23 or minute > 59:
        raise ValueError("BACKUP_TIME must be a valid 24-hour HHMM time")
    return hour, minute


def cron_line(destination: Path, backup_time: str) -> str:
    """Build one daily host command with the tools backup.py needs on PATH."""
    hour, minute = parse_time(backup_time)
    tools = {name: shutil.which(name) for name in ("make", "python3", "openssl", "ssh")}
    missing = [name for name, path in tools.items() if path is None]
    if missing:
        raise ValueError(f"missing host tools: {', '.join(missing)}")
    log = destination / "backup.log"
    if any(char in str(path) for path in (ROOT, log) for char in ("%", "\n")):
        raise ValueError("project and backup paths cannot contain % or newlines for cron")
    path_dirs = dict.fromkeys(str(Path(path).parent) for path in tools.values())
    search_path = ":".join(path_dirs)
    return (
        f"{minute} {hour} * * * umask 077; PATH={shlex.quote(search_path)} "
        f"{shlex.quote(tools['make'])} -C {shlex.quote(str(ROOT))} backup "
        f">> {shlex.quote(str(log))} 2>&1 {MARKER}"
    )


def install(backup_time: str) -> None:
    """Replace only this project's marked cron entry, leaving other jobs alone."""
    parse_time(backup_time)
    destination = backup_dir()
    password_file()
    crontab = shutil.which("crontab")
    if crontab is None:
        raise ValueError("crontab is not installed on this host")
    current = subprocess.run([crontab, "-l"], capture_output=True, text=True)
    if current.returncode == 0:
        existing = current.stdout.splitlines()
    elif current.returncode == 1 and "no crontab for" in current.stderr:
        existing = []
    else:
        raise RuntimeError(f"cannot read host crontab: {current.stderr.strip()}")

    entry = cron_line(destination, backup_time)
    other_lines = [line for line in existing if not line.rstrip().endswith(MARKER)]
    updated = "\n".join([*other_lines, entry]) + "\n"
    if updated == current.stdout:
        print("daily backup cron entry already installed")
        return
    subprocess.run([crontab, "-"], input=updated, text=True, check=True,
                   capture_output=True)
    print(f"installed daily {backup_time[:2]}:{backup_time[2:]} host backup cron entry")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--time", default="0200", help="daily backup time as 24-hour HHMM")
    args = parser.parse_args()
    try:
        install(args.time)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"backup schedule: {error}", file=sys.stderr)
        sys.exit(1)
