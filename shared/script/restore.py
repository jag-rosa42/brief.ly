#!/usr/bin/env python3
"""Restore one host backup set into a fresh, empty QEMU VM."""

import argparse
import getpass
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile

import backup


DATABASE_INSTANCES = ("pgsql", "pgvector")


def target_port(raw: str) -> int:
    if not raw.isdecimal() or not 1 <= int(raw) <= 65535:
        raise ValueError("VM_SSH_PORT must be a TCP port number")
    return int(raw)


def validate_target_vm(raw: str, port: int) -> Path:
    """Make sure the configured SSH port belongs to the configured VM disk."""
    vm_dir = Path(raw).expanduser().resolve()
    if not vm_dir.is_dir():
        raise ValueError("VM_DIR must be an existing VM directory")

    disks = list(vm_dir.glob("ubuntu-server-cloud-*.qcow2"))
    if len(disks) != 1:
        raise ValueError("VM_DIR must contain exactly one QEMU guest disk")

    # A listening port alone does not identify the VM. Its process must also
    # have the one disk in VM_DIR open before we send restore commands to it.
    listener = subprocess.run(
        ["lsof", "-nP", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if len(listener) != 1:
        raise ValueError("VM_SSH_PORT must have exactly one listener")
    owned = subprocess.run(
        ["lsof", "-nP", "-a", "-p", listener[0], str(disks[0])],
        capture_output=True, text=True,
    )
    if owned.returncode:
        raise ValueError("VM_SSH_PORT is not held by VM_DIR's QEMU disk")
    return vm_dir


def ssh_args(port: int, command: str) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=5", "-p", str(port),
            f"{getpass.getuser()}@127.0.0.1", command]


def remote(port: int, argv: list[str], *, stdin: Path | None = None) -> str:
    """Run one command in the guest, optionally streaming a host file to it."""
    command = shlex.join(argv)
    if stdin is None:
        result = subprocess.run(ssh_args(port, command), capture_output=True, text=True)
    else:
        with stdin.open("rb") as source:
            result = subprocess.run(ssh_args(port, command), stdin=source,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if isinstance(result.stderr, bytes) else result.stderr
        raise RuntimeError(f"target VM command failed: {stderr.strip()}")
    return result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout


def guest_command(remote_dir: str, command: str) -> list[str]:
    return ["sh", "-c", f"cd {shlex.quote(remote_dir)} && {command}"]


def check_empty_cluster(port: int, instance: str, db_user: str) -> None:
    """Reject a target with application databases or tables in postgres."""
    psql = ["docker", "exec", "-u", "postgres", instance,
            "psql", "-U", db_user, "-d", "postgres", "-Atqc"]
    names = set(remote(port, psql + [backup.SQL_DATABASES]).splitlines())
    if names != {"postgres"}:
        raise ValueError(f"{instance} target is not empty: databases {sorted(names)}")

    table_count_sql = (
        "SELECT count(*) FROM pg_class WHERE relkind IN ('r','p') "
        "AND relnamespace NOT IN (SELECT oid FROM pg_namespace "
        "WHERE nspname IN ('pg_catalog','information_schema'))"
    )
    if remote(port, psql + [table_count_sql]).strip() != "0":
        raise ValueError(f"{instance} postgres database contains tables")


def check_empty_prometheus(port: int, domain: str) -> None:
    """Require a new volume so restored history cannot mix with live data."""
    volume = f"{domain}_prometheus_data"
    command = shlex.join(["docker", "volume", "inspect", volume])
    result = subprocess.run(ssh_args(port, command), capture_output=True)
    if result.returncode == 0:
        raise ValueError(f"target Prometheus volume already exists: {volume}")


def preflight(port: int, remote_dir: str, members: list[dict], db_user: str,
              domain: str) -> None:
    """Require two initialized but unused clusters and a new TSDB volume."""
    if not remote_dir.startswith("/") or remote_dir == "/":
        raise ValueError("VM_REMOTE_DIR must be an absolute guest project path")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", db_user):
        raise ValueError("POSTGRES_USER must be a simple SQL identifier")
    for instance in DATABASE_INSTANCES:
        expected = {m["database"] for m in members if m.get("instance") == instance
                    and "database" in m}
        if "postgres" not in expected:
            raise ValueError(f"backup has no {instance} postgres database")
        check_empty_cluster(port, instance, db_user)

    check_empty_prometheus(port, domain)
    if not any(m.get("kind") == "prometheus-tsdb" for m in members):
        raise ValueError("backup has no Prometheus snapshot")
    remote(port, guest_command(remote_dir, "test -f compose.monitoring.yaml"))


def globals_for_bootstrap(path: Path, user: str, destination: Path) -> None:
    """The fresh image already creates POSTGRES_USER; retain its ALTER ROLE."""
    statement = f"CREATE ROLE {user};"
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    if lines.count(statement + "\n") != 1:
        raise ValueError(f"globals do not contain exactly one bootstrap role: {user}")
    destination.write_text("".join(line for line in lines if line != statement + "\n"))
    destination.chmod(0o600)


def restore_instance(port: int, directory: Path, members: list[dict],
                     instance: str, db_user: str) -> None:
    """Restore one instance's roles, then its postgres and other databases."""
    globals_file = next(directory / member["file"] for member in members
                        if member.get("instance") == instance
                        and member.get("kind") == "globals")
    with tempfile.TemporaryDirectory(prefix="restore-globals-") as temporary:
        prepared = Path(temporary) / "globals.sql"
        globals_for_bootstrap(globals_file, db_user, prepared)
        remote(port, ["docker", "exec", "-i", "-u", "postgres", instance,
                      "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", db_user,
                      "-d", "postgres"], stdin=prepared)

    databases = [member for member in members
                 if member.get("instance") == instance and "database" in member]
    # The bootstrap postgres database already exists. Restore it first, then
    # create and restore the remaining databases in a repeatable order.
    databases.sort(key=lambda member: (member["database"] != "postgres",
                                       member["database"]))
    for member in databases:
        name = member["database"]
        if name != "postgres":
            remote(port, ["docker", "exec", "-u", "postgres", instance,
                          "createdb", "-U", db_user, name])
        remote(port, ["docker", "exec", "-i", "-u", "postgres", instance,
                      "pg_restore", "--exit-on-error", "-U", db_user,
                      "-d", name], stdin=directory / member["file"])
        print(f"restored {instance}/{name}")


def restore_databases(port: int, directory: Path, members: list[dict], db_user: str) -> None:
    for instance in DATABASE_INSTANCES:
        restore_instance(port, directory, members, instance, db_user)


def restore_prometheus(port: int, remote_dir: str, directory: Path,
                       members: list[dict]) -> None:
    remote(port, guest_command(remote_dir, "make shared-networks monitoring-storage"))
    remote(port, guest_command(remote_dir,
                               "docker compose -f compose.monitoring.yaml create prometheus"))
    snapshot = next(directory / m["file"] for m in members
                    if m.get("kind") == "prometheus-tsdb")
    with tarfile.open(snapshot) as archive:
        members_in_snapshot = archive.getmembers()
        # docker cp extracts this tar inside the container, so reject paths
        # that could escape the intended Prometheus data directory.
        if not members_in_snapshot or any(
            item.name.startswith("/") or ".." in Path(item.name).parts
            for item in members_in_snapshot
        ):
            raise ValueError("unsafe Prometheus snapshot")
    remote(port, ["docker", "cp", "-", "prometheus:/prometheus"], stdin=snapshot)
    print("restored Prometheus TSDB; monitoring can now start")


def restore(name: str, remote_dir: str) -> None:
    """Verify the backup and configured VM, then import both data stores."""
    destination = backup.backup_dir()
    port = target_port(backup.setting("VM_SSH_PORT", "2222"))
    vm_dir = backup.setting("VM_DIR", str(backup.ROOT / "vm"))
    validate_target_vm(vm_dir, port)
    if name not in backup.complete_sets(destination):
        raise ValueError("choose a completed backup set from backup-list")
    user = backup.setting("POSTGRES_USER")
    domain = backup.setting("DOMAIN")
    with tempfile.TemporaryDirectory(prefix="restore-set-") as temporary:
        stage = Path(temporary) / "extracted"
        backup.extract_set(destination, name, stage)
        manifest = json.loads((stage / "manifest.json").read_text())
        members = manifest["members"]
        preflight(port, remote_dir, members, user, domain)
        restore_databases(port, stage, members, user)
        restore_prometheus(port, remote_dir, stage, members)
    print(f"restore complete on {vm_dir}; verify records and historical metrics before use")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_set")
    parser.add_argument("--remote-dir", required=True,
                        help="project directory inside the configured VM")
    args = parser.parse_args()
    try:
        restore(args.backup_set, args.remote_dir)
    except (ValueError, OSError, RuntimeError, StopIteration, subprocess.CalledProcessError,
            tarfile.TarError) as error:
        print(f"restore: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
