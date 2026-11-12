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


def target_port(raw: str, *, in_place: bool = False) -> int:
    if not raw.isdecimal() or not 1 <= int(raw) <= 65535:
        raise ValueError("TARGET_VM_SSH_PORT must be a TCP port number")
    port = int(raw)
    source_port = int(backup.setting("VM_SSH_PORT", "2222"))
    if in_place and port != source_port:
        raise ValueError("in-place restore must use the configured VM SSH port")
    if not in_place and port == source_port:
        raise ValueError("restore target must use a different SSH port from the source VM")
    return port


def validate_target_vm(raw: str, port: int, *, in_place: bool = False) -> Path:
    """Match the listening QEMU process to the explicitly named target disk."""
    vm_dir = Path(raw).expanduser().resolve()
    source = Path(backup.setting("VM_DIR", str(backup.ROOT / "vm"))).resolve()
    if not vm_dir.is_dir():
        raise ValueError("TARGET_VM_DIR must be an existing VM directory")
    if in_place and vm_dir != source:
        raise ValueError("in-place restore must use the configured VM_DIR")
    if not in_place and vm_dir == source:
        raise ValueError("restore target must be separate from the source VM_DIR")
    disks = list(vm_dir.glob("ubuntu-server-cloud-*.qcow2"))
    if len(disks) != 1:
        raise ValueError("TARGET_VM_DIR must contain exactly one QEMU guest disk")
    listener = subprocess.run(
        ["lsof", "-nP", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if len(listener) != 1:
        raise ValueError("target SSH port must have exactly one listener")
    owned = subprocess.run(
        ["lsof", "-nP", "-a", "-p", listener[0], str(disks[0])],
        capture_output=True, text=True,
    )
    if owned.returncode:
        raise ValueError("target SSH port is not held by TARGET_VM_DIR's QEMU disk")
    return vm_dir


def ssh_args(port: int, command: str) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=5", "-p", str(port),
            f"{getpass.getuser()}@127.0.0.1", command]


def remote(port: int, argv: list[str], *, stdin: Path | None = None) -> str:
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


def preflight(port: int, remote_dir: str, members: list[dict], db_user: str,
              domain: str) -> None:
    """Require two initialized but unused clusters and a new TSDB volume."""
    if not remote_dir.startswith("/") or remote_dir == "/":
        raise ValueError("TARGET_VM_REMOTE_DIR must be an absolute guest project path")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", db_user):
        raise ValueError("POSTGRES_USER must be a simple SQL identifier")
    for instance in ("pgsql", "pgvector"):
        expected = {m["database"] for m in members if m.get("instance") == instance
                    and "database" in m}
        if "postgres" not in expected:
            raise ValueError(f"backup has no {instance} postgres database")
        names = set(remote(port, ["docker", "exec", "-u", "postgres", instance,
                                  "psql", "-U", db_user, "-d", "postgres", "-Atqc",
                                  backup.SQL_DATABASES]).splitlines())
        if names != {"postgres"}:
            raise ValueError(f"{instance} target is not empty: databases {sorted(names)}")
        tables = remote(port, ["docker", "exec", "-u", "postgres", instance,
                               "psql", "-U", db_user, "-d", "postgres", "-Atqc",
                               "SELECT count(*) FROM pg_class WHERE relkind IN ('r','p') "
                               "AND relnamespace NOT IN (SELECT oid FROM pg_namespace "
                               "WHERE nspname IN ('pg_catalog','information_schema'))"])
        if tables.strip() != "0":
            raise ValueError(f"{instance} postgres database contains tables")
    volume = f"{domain}_prometheus_data"
    result = subprocess.run(ssh_args(port, shlex.join(["docker", "volume", "inspect", volume])),
                            capture_output=True)
    if result.returncode == 0:
        raise ValueError(f"target Prometheus volume already exists: {volume}")
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


def restore_databases(port: int, directory: Path, members: list[dict], db_user: str) -> None:
    for instance in ("pgsql", "pgvector"):
        globals_file = next(directory / m["file"] for m in members
                            if m.get("instance") == instance and m.get("kind") == "globals")
        with tempfile.TemporaryDirectory(prefix="restore-globals-") as temporary:
            prepared = Path(temporary) / "globals.sql"
            globals_for_bootstrap(globals_file, db_user, prepared)
            remote(port, ["docker", "exec", "-i", "-u", "postgres", instance,
                          "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", db_user,
                          "-d", "postgres"], stdin=prepared)
        databases = [m for m in members if m.get("instance") == instance and "database" in m]
        for member in sorted(databases, key=lambda m: (m["database"] != "postgres", m["database"])):
            name = member["database"]
            if name != "postgres":
                remote(port, ["docker", "exec", "-u", "postgres", instance,
                              "createdb", "-U", db_user, name])
            remote(port, ["docker", "exec", "-i", "-u", "postgres", instance,
                          "pg_restore", "--exit-on-error", "-U", db_user,
                          "-d", name], stdin=directory / member["file"])
            print(f"restored {instance}/{name}")


def restore_prometheus(port: int, remote_dir: str, directory: Path,
                       members: list[dict]) -> None:
    remote(port, guest_command(remote_dir, "make shared-networks monitoring-storage"))
    remote(port, guest_command(remote_dir,
                               "docker compose -f compose.monitoring.yaml create prometheus"))
    snapshot = next(directory / m["file"] for m in members
                    if m.get("kind") == "prometheus-tsdb")
    with tarfile.open(snapshot) as archive:
        if not archive.getmembers() or any(
            item.name.startswith("/") or ".." in Path(item.name).parts for item in archive
        ):
            raise ValueError("unsafe Prometheus snapshot")
    remote(port, ["docker", "cp", "-", "prometheus:/prometheus"], stdin=snapshot)
    print("restored Prometheus TSDB; start monitoring after verification")


def restore(name: str, port: int, vm_dir: str, remote_dir: str,
            *, in_place: bool = False) -> None:
    destination = backup.backup_dir()
    target_port(str(port), in_place=in_place)
    validate_target_vm(vm_dir, port, in_place=in_place)
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
    parser.add_argument("--target-vm-dir", required=True)
    parser.add_argument("--target-ssh-port", required=True)
    parser.add_argument("--target-remote-dir", required=True)
    parser.add_argument("--in-place", action="store_true",
                        help="require the configured VM_DIR and SSH port")
    args = parser.parse_args()
    try:
        port = target_port(args.target_ssh_port, in_place=args.in_place)
        restore(args.backup_set, port, args.target_vm_dir, args.target_remote_dir,
                in_place=args.in_place)
    except (ValueError, OSError, RuntimeError, StopIteration, subprocess.CalledProcessError,
            tarfile.TarError) as error:
        print(f"restore: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
