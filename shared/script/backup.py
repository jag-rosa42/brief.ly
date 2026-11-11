#!/usr/bin/env python3
"""Host-side, encrypted backup of both PostgreSQL instances and Prometheus."""

import argparse
import datetime as dt
import getpass
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PASSWORD_FILE = Path.home() / ".config/ft_transcendance/backup_password"
PBKDF2_ROUNDS = 200_000
SQL_DATABASES = (
    "SELECT datname FROM pg_database "
    "WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
SET_NAME = re.compile(r"^backup-(\d{8}T\d{6}Z)-[0-9a-f]{8}$")


def setting(name: str, default: str | None = None) -> str:
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(name + "="):
            values[name] = line.split("=", 1)[1]
    value = os.environ.get(name, values.get(name, default))
    if not value:
        raise ValueError(f"{name} must be set")
    return value.replace("$(CURDIR)", str(ROOT)).replace("$(HOME)", str(Path.home()))


def validate_backup_path(raw: str, vm_dir: str) -> Path:
    """Resolve a host path and reject destinations inside the guest VM files."""
    destination = Path(raw)
    if not destination.is_absolute():
        raise ValueError("BACKUP_HOST_DIR must be an absolute host path")
    # Resolve symlinks so a path that points into VM_DIR is rejected too.
    destination = destination.resolve()
    vm_path = Path(vm_dir).resolve()
    if destination == vm_path or vm_path in destination.parents:
        raise ValueError("BACKUP_HOST_DIR must be outside VM_DIR")
    return destination


def backup_dir() -> Path:
    """Prepare the private host directory that will hold completed sets."""
    raw = setting("BACKUP_HOST_DIR")
    vm_dir = setting("VM_DIR", str(ROOT / "vm"))
    path = validate_backup_path(raw, vm_dir)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError("BACKUP_HOST_DIR must be private (chmod 700)")
    if not os.access(path, os.W_OK):
        raise ValueError("BACKUP_HOST_DIR is not writable")
    return path


def password_file() -> Path:
    path = Path(setting("BACKUP_PASSWORD_FILE", str(PASSWORD_FILE))).expanduser()
    if not path.is_file() or not path.read_bytes().splitlines()[0:1]:
        raise ValueError(f"backup password file missing or empty: {path}")
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError("backup password file must be private (chmod 600)")
    return path


def password_bytes(path: Path) -> bytes:
    # OpenSSL's `-pass file:` reads the first line only. Use the same bytes for
    # the independent HMAC key so a restored password file is unambiguous.
    return path.read_bytes().splitlines()[0]


def remote_args(command: str) -> list[str]:
    port = setting("VM_SSH_PORT", "2222")
    if not port.isdigit():
        raise ValueError("VM_SSH_PORT must be numeric")
    user = getpass.getuser()
    return [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=5",
        "-p", port, f"{user}@127.0.0.1", command,
    ]


def capture_remote(argv: list[str]) -> bytes:
    """Run a VM command over SSH and return its short text output."""
    result = subprocess.run(remote_args(shlex.join(argv)), capture_output=True)
    if result.returncode:
        raise RuntimeError(f"VM command failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def stream_remote(command: str, destination: Path) -> None:
    """Stream a VM command's output directly into a host file."""
    with destination.open("wb") as output:
        result = subprocess.run(remote_args(command), stdout=output, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f"VM command failed: {result.stderr.decode(errors='replace').strip()}")
    if not destination.stat().st_size:
        raise RuntimeError("VM command returned an empty backup file")


def dump_database(stage: Path, instance: str, db_user: str, name: str,
                  index: int) -> dict[str, str]:
    """Run pg_dump in one VM container and save its output on the host."""
    path = stage / f"{instance}-db-{index:03d}.dump"
    # -Fc includes the database's schema and rows in a pg_restore-readable file.
    command = [
        "docker", "exec", "-u", "postgres", instance,
        "pg_dump", "-Fc", "-U", db_user, "-d", name,
    ]
    stream_remote(shlex.join(command), path)
    return {"file": path.name, "instance": instance, "database": name}


def list_databases(instance: str, db_user: str) -> list[str]:
    """Ask one PostgreSQL instance which non-template databases it contains."""
    # psql prints one database name per line for the SQL query above.
    command = [
        "docker", "exec", "-u", "postgres", instance, "psql",
        "-U", db_user, "-d", "postgres", "-Atqc", SQL_DATABASES,
    ]
    names = capture_remote(command).decode().splitlines()
    if not names or any(not name for name in names) or len(set(names)) != len(names):
        raise RuntimeError(f"{instance}: database list is empty or invalid")
    return names


def dump_globals(stage: Path, instance: str, db_user: str) -> dict[str, str]:
    """Save cluster roles and other globals separately from database dumps."""
    path = stage / f"{instance}-globals.sql"
    # Database dumps refer to roles but do not create them.
    command = [
        "docker", "exec", "-u", "postgres", instance,
        "pg_dumpall", "--globals-only", "-U", db_user,
    ]
    stream_remote(shlex.join(command), path)
    return {"file": path.name, "instance": instance, "kind": "globals"}


def snapshot_prometheus(stage: Path) -> dict[str, str]:
    """Copy Prometheus's TSDB while it is stopped, then restart it."""
    path = stage / "prometheus.tar"
    # Avoid reading live TSDB files; the trap restarts Prometheus if copy fails.
    command = (
        "set -eu; docker stop prometheus >/dev/null; "
        "trap 'docker start prometheus >/dev/null' EXIT; "
        "docker cp prometheus:/prometheus/. -; "
        "docker start prometheus >/dev/null; trap - EXIT"
    )
    stream_remote(command, path)
    with tarfile.open(path) as archive:
        if not archive.getmembers():
            raise RuntimeError("Prometheus snapshot is empty")
    return {"file": path.name, "kind": "prometheus-tsdb"}


def collect(stage: Path) -> list[dict[str, str]]:
    """Gather both clusters' dumps and Prometheus history in a temporary directory."""
    members = []
    db_user = setting("POSTGRES_USER")
    for instance in ("pgsql", "pgvector"):
        for index, name in enumerate(list_databases(instance, db_user)):
            members.append(dump_database(stage, instance, db_user, name, index))
        members.append(dump_globals(stage, instance, db_user))

    # A missing Prometheus container fails the run; database-only sets are incomplete.
    members.append(snapshot_prometheus(stage))
    return members


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_archive(stage: Path, members: list[dict[str, str]], output: Path) -> None:
    manifest = {"format": 1, "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                             capture_output=True, text=True, check=True).stdout.strip(),
                "members": []}
    with tarfile.open(output, "w:gz") as archive:
        for member in members:
            path = stage / member["file"]
            entry = {**member, "sha256": sha256(path), "size": path.stat().st_size}
            manifest["members"].append(entry)
            archive.add(path, arcname=path.name, recursive=False)
        data = json.dumps(manifest, sort_keys=True).encode()
        info = tarfile.TarInfo("manifest.json")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))


def mac_for(path: Path, key: bytes) -> str:
    digest = hmac.new(key, digestmod=hashlib.sha256)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encrypt(source: Path, target: Path, password: Path) -> dict[str, str | int]:
    # OpenSSL encrypts with a salted PBKDF2-derived AES key. An independent
    # PBKDF2-derived HMAC key authenticates the ciphertext before decryption.
    subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", str(PBKDF2_ROUNDS),
        "-salt", "-pass", f"file:{password}", "-in", str(source), "-out", str(target),
    ], check=True, capture_output=True)
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password_bytes(password), salt, PBKDF2_ROUNDS)
    return {"format": 1, "rounds": PBKDF2_ROUNDS, "mac_salt": salt.hex(),
            "mac": mac_for(target, key)}


def verify_set(ciphertext: Path, metadata: Path, password: Path) -> None:
    info = json.loads(metadata.read_text())
    if info.get("format") != 1 or info.get("rounds") != PBKDF2_ROUNDS:
        raise ValueError("unknown backup metadata format")
    key = hashlib.pbkdf2_hmac("sha256", password_bytes(password),
                             bytes.fromhex(info["mac_salt"]), PBKDF2_ROUNDS)
    if not hmac.compare_digest(mac_for(ciphertext, key), info["mac"]):
        raise ValueError("backup authentication failed")
    with tempfile.TemporaryDirectory(prefix="backup-verify-") as directory:
        archive_path = Path(directory) / "archive.tar.gz"
        decrypt(ciphertext, archive_path, password)
        with tarfile.open(archive_path) as archive:
            manifest = json.load(archive.extractfile("manifest.json"))
            if manifest.get("format") != 1 or not manifest.get("members"):
                raise ValueError("backup manifest is missing members")
            for member in manifest["members"]:
                source = archive.extractfile(member["file"])
                if source is None:
                    raise ValueError(f"backup member missing: {member['file']}")
                digest = hashlib.sha256()
                size = 0
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
                if digest.hexdigest() != member["sha256"] or size != member["size"]:
                    raise ValueError(f"backup member damaged: {member['file']}")


def decrypt(ciphertext: Path, archive_path: Path, password: Path) -> None:
    subprocess.run([
        "openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
        "-iter", str(PBKDF2_ROUNDS), "-pass", f"file:{password}",
        "-in", str(ciphertext), "-out", str(archive_path),
    ], check=True, capture_output=True)


def extract_set(directory: Path, name: str, target: Path) -> None:
    if not SET_NAME.fullmatch(name) or name not in complete_sets(directory):
        raise ValueError("choose a completed backup set from backup-list")
    if not target.is_absolute():
        raise ValueError("TARGET_DIR must be an absolute host path")
    target = target.resolve()
    if target.exists():
        raise ValueError("TARGET_DIR already exists; choose a new directory")
    if target == directory or directory in target.parents:
        raise ValueError("TARGET_DIR must be outside BACKUP_HOST_DIR")
    if not target.parent.is_dir():
        raise ValueError("TARGET_DIR parent directory does not exist")
    lock = directory / ".backup.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RuntimeError("cannot extract while a backup or prune is running") from error
    try:
        password = password_file()
        ciphertext = directory / f"{name}.enc"
        verify_set(ciphertext, directory / f"{name}.json", password)
        target.mkdir(mode=0o700)
        marker = target / ".incomplete"
        marker.write_text("Extraction did not finish. Do not use these files.\n")
        archive_path = target / ".archive.tar.gz"
        decrypt(ciphertext, archive_path, password)
        with tarfile.open(archive_path) as archive:
            manifest_data = archive.extractfile("manifest.json").read()
            manifest = json.loads(manifest_data)
            names = [member["file"] for member in manifest["members"]]
            if len(names) != len(set(names)) or any(
                Path(item).name != item or item in ("manifest.json", ".incomplete", ".archive.tar.gz")
                for item in names
            ):
                raise ValueError("unsafe backup member names")
            for item in names:
                source = archive.extractfile(item)
                with (target / item).open("wb") as output:
                    shutil.copyfileobj(source, output)
                (target / item).chmod(0o600)
            (target / "manifest.json").write_bytes(manifest_data)
            (target / "manifest.json").chmod(0o600)
        archive_path.unlink()
        marker.unlink()
        print(f"extracted {name} to {target}")
    finally:
        lock.rmdir()


def backup() -> str:
    """Create one verified set while holding the destination's backup lock."""
    destination = backup_dir()
    password = password_file()
    # Atomic directory creation prevents concurrent backup runs.
    lock = destination / ".backup.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RuntimeError("another backup is running (.backup.lock exists)") from error
    try:
        with tempfile.TemporaryDirectory(prefix=".backup-stage-", dir=destination) as directory:
            stage = Path(directory)
            members = collect(stage)

            # Pack the dumps and a manifest with each file's size and checksum.
            plain = stage / "complete.tar.gz"
            create_archive(stage, members, plain)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            name = f"backup-{stamp}-{secrets.token_hex(4)}"
            encrypted = stage / f"{name}.enc"
            metadata = stage / f"{name}.json"

            # Encrypt the archive; the sidecar holds authentication data, not the password.
            authentication = encrypt(plain, encrypted, password)
            encrypted.chmod(0o600)
            metadata.write_text(json.dumps(authentication, sort_keys=True))
            metadata.chmod(0o600)

            # Check the encrypted file and every archived member before publishing either file.
            verify_set(encrypted, metadata, password)
            shutil.move(str(encrypted), destination / encrypted.name)
            # Publish the sidecar last: listing requires both files to exist.
            shutil.move(str(metadata), destination / metadata.name)
            print(f"completed and verified: {name}")
            return name
    finally:
        lock.rmdir()


def write_status(directory: Path, outcome: str, completed_set: str | None) -> None:
    """Atomically record this run without losing the last successful set."""
    path = directory / "backup-status.json"
    previous = json.loads(path.read_text()) if path.is_file() else {}
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    status = {
        "last_run_utc": now,
        "last_run_outcome": outcome,
        "last_success_utc": now if outcome == "success" else previous.get("last_success_utc"),
        "last_success_set": completed_set if completed_set else previous.get("last_success_set"),
    }
    with tempfile.NamedTemporaryFile(
        mode="w", prefix=".backup-status-", suffix=".tmp", dir=directory,
        delete=False,
    ) as output:
        temporary = Path(output.name)
        output.write(json.dumps(status, sort_keys=True) + "\n")
    try:
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_backup() -> None:
    """Run a backup and record success or failure for manual and cron use."""
    directory = backup_dir()
    try:
        completed_set = backup()
    except Exception:
        write_status(directory, "failure", None)
        raise
    write_status(directory, "success", completed_set)


def complete_sets(directory: Path) -> list[str]:
    """List only published sets with both required files."""
    return sorted(
        metadata.stem for metadata in directory.glob("backup-*.json")
        if SET_NAME.fullmatch(metadata.stem) and metadata.with_suffix(".enc").is_file()
    )


def retention_plan(names: list[str]) -> tuple[list[str], list[str]]:
    """Keep newest per 7 UTC dates, 4 ISO weeks, and 3 calendar months."""
    # Newest first lets one set represent a day, its week, and its month.
    ordered = sorted(names, reverse=True)
    if len(ordered) != len(set(ordered)):
        raise ValueError("duplicate backup set names")
    dates = {}
    for name in ordered:
        match = SET_NAME.fullmatch(name)
        if match is None:
            raise ValueError(f"invalid backup set name: {name}")
        dates[name] = dt.datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").date()
    keep = set()
    # Take the union of the daily, weekly, and monthly choices.
    for limit, bucket in (
        (7, lambda day: day),
        (4, lambda day: day.isocalendar()[:2]),
        (3, lambda day: (day.year, day.month)),
    ):
        seen = set()
        for name in ordered:
            period = bucket(dates[name])
            if period not in seen and len(seen) < limit:
                keep.add(name)
                seen.add(period)
    return ([name for name in ordered if name in keep],
            [name for name in ordered if name not in keep])


def _prune_locked(directory: Path, apply: bool) -> None:
    names = complete_sets(directory)
    if not names:
        raise RuntimeError("no completed backup sets to retain")
    keep, remove = retention_plan(names)
    # A bad newest set must not trigger deletion of older recovery points.
    verify_set(directory / f"{names[-1]}.enc",
               directory / f"{names[-1]}.json", password_file())
    sizes = {
        name: (directory / f"{name}.enc").stat().st_size
        + (directory / f"{name}.json").stat().st_size
        for name in names
    }
    free = shutil.disk_usage(directory).free
    print(f"completed sets: {len(names)}; stored: {sum(sizes.values())} bytes; "
          f"host free: {free} bytes")
    print(f"largest set: {max(sizes.values())} bytes; "
          f"candidate reclaim: {sum(sizes[name] for name in remove)} bytes")
    for name in keep:
        print(f"KEEP         {name}")
    for name in remove:
        print(f"{'REMOVE      ' if apply else 'WOULD REMOVE'} {name}")
    if not apply:
        print("preview only; nothing deleted (use APPLY=1 to remove candidates)")
        return
    for name in remove:
        # Remove the listing marker first, so an interrupted prune cannot
        # expose a half-deleted set as complete. The ciphertext may remain as
        # an orphan if interrupted, but no retained set is affected.
        (directory / f"{name}.json").unlink()
        (directory / f"{name}.enc").unlink()
    print(f"removed {len(remove)} older completed sets")


def prune(directory: Path, apply: bool) -> None:
    lock = directory / ".backup.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RuntimeError("cannot prune while a backup or prune is running") from error
    try:
        _prune_locked(directory, apply)
    finally:
        lock.rmdir()


def parse_arguments() -> argparse.Namespace:
    """Read the command and its optional arguments from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("backup", "list", "verify", "retention-preview", "prune", "extract"))
    parser.add_argument("backup_set", nargs="?", help="backup name for verify or extract")
    parser.add_argument("target_dir", nargs="?", help="new absolute host directory for extract")
    parser.add_argument("--apply", action="store_true", help="delete prune candidates")
    return parser.parse_args()


def run_command(args: argparse.Namespace) -> None:
    """Select the backup operation requested by the user or scheduler."""
    directory = backup_dir()
    if args.command == "backup":
        run_backup()
    elif args.command == "list":
        for name in complete_sets(directory):
            print(name)
    elif args.command == "retention-preview":
        keep, remove = retention_plan(complete_sets(directory))
        for name in keep:
            print(f"KEEP         {name}")
        for name in remove:
            print(f"WOULD REMOVE {name}")
        print(f"{len(keep)} kept, {len(remove)} candidates; nothing deleted")
    elif args.command == "prune":
        prune(directory, args.apply)
    elif args.command == "extract":
        if not args.backup_set or not args.target_dir:
            raise ValueError("extract needs a backup set name and TARGET_DIR")
        extract_set(directory, args.backup_set, Path(args.target_dir))
    elif args.command == "verify":
        if not args.backup_set or Path(args.backup_set).name != args.backup_set:
            raise ValueError("verify needs a backup set name from list")
        verify_set(directory / f"{args.backup_set}.enc",
                   directory / f"{args.backup_set}.json", password_file())
        print(f"verified: {args.backup_set}")


def main() -> int:
    args = parse_arguments()
    try:
        run_command(args)
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError,
            tarfile.TarError) as error:
        print(f"backup: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
