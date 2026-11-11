import importlib.util
import contextlib
import io
import json
from pathlib import Path
import shlex
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "backup.py"
spec = importlib.util.spec_from_file_location("host_backup", SCRIPT)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.password = self.root / "password"
        self.password.write_text("test-only-password-long-enough-to-derive-keys\n")
        self.password.chmod(0o600)

    def test_backup_destination_must_be_absolute_and_outside_vm(self):
        vm_dir = self.root / "vm"
        host_dir = self.root / "backups"
        self.assertEqual(
            backup.validate_backup_path(str(host_dir), str(vm_dir)),
            host_dir.resolve(),
        )
        with self.assertRaisesRegex(ValueError, "absolute host path"):
            backup.validate_backup_path("backups", str(vm_dir))
        with self.assertRaisesRegex(ValueError, "outside VM_DIR"):
            backup.validate_backup_path(str(vm_dir / "backups"), str(vm_dir))

    def test_backup_directory_is_created_private(self):
        host_dir = self.root / "backups"
        settings = {"BACKUP_HOST_DIR": str(host_dir), "VM_DIR": str(self.root / "vm")}
        with mock.patch.object(backup, "setting", side_effect=lambda name, default=None: settings[name]):
            self.assertEqual(backup.backup_dir(), host_dir.resolve())
        self.assertEqual(host_dir.stat().st_mode & 0o777, 0o700)

    def test_one_database_dump_uses_custom_format_and_host_file(self):
        commands = []

        def save_dump(command, destination):
            commands.append(shlex.split(command))
            destination.write_bytes(b"test dump")

        with mock.patch.object(backup, "stream_remote", side_effect=save_dump):
            member = backup.dump_database(
                self.root, "pgsql", "transcendence", "identity_db", 0,
            )

        self.assertEqual(commands, [[
            "docker", "exec", "-u", "postgres", "pgsql",
            "pg_dump", "-Fc", "-U", "transcendence", "-d", "identity_db",
        ]])
        self.assertEqual(member, {
            "file": "pgsql-db-000.dump", "instance": "pgsql", "database": "identity_db",
        })
        self.assertTrue((self.root / member["file"]).is_file())

    def test_database_list_excludes_templates_and_rejects_bad_results(self):
        with mock.patch.object(backup, "capture_remote", return_value=b"postgres\nidentity_db\n") as capture:
            self.assertEqual(
                backup.list_databases("pgsql", "transcendence"),
                ["postgres", "identity_db"],
            )
        command = capture.call_args.args[0]
        self.assertEqual(command[:5], ["docker", "exec", "-u", "postgres", "pgsql"])
        self.assertIn("NOT datistemplate", command[-1])
        for invalid in (b"", b"identity_db\nidentity_db\n"):
            with mock.patch.object(backup, "capture_remote", return_value=invalid):
                with self.assertRaisesRegex(RuntimeError, "database list is empty or invalid"):
                    backup.list_databases("pgsql", "transcendence")

    def test_globals_dump_saves_roles_in_a_separate_host_file(self):
        commands = []

        def save_globals(command, destination):
            commands.append(shlex.split(command))
            destination.write_bytes(b"CREATE ROLE transcendence;\n")

        with mock.patch.object(backup, "stream_remote", side_effect=save_globals):
            member = backup.dump_globals(self.root, "pgvector", "transcendence")
        self.assertEqual(commands, [[
            "docker", "exec", "-u", "postgres", "pgvector",
            "pg_dumpall", "--globals-only", "-U", "transcendence",
        ]])
        self.assertEqual(member, {
            "file": "pgvector-globals.sql", "instance": "pgvector", "kind": "globals",
        })
        self.assertTrue((self.root / member["file"]).is_file())

    def test_prometheus_snapshot_stops_copies_and_restarts(self):
        commands = []

        def save_snapshot(command, destination):
            commands.append(command)
            with tarfile.open(destination, "w") as archive:
                data = b"historical sample block"
                info = tarfile.TarInfo("sample-block")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

        with mock.patch.object(backup, "stream_remote", side_effect=save_snapshot):
            member = backup.snapshot_prometheus(self.root)

        self.assertEqual(member, {"file": "prometheus.tar", "kind": "prometheus-tsdb"})
        self.assertLess(commands[0].index("docker stop prometheus"),
                        commands[0].index("docker cp prometheus:/prometheus/. -"))
        self.assertLess(commands[0].index("docker cp prometheus:/prometheus/. -"),
                        commands[0].rindex("docker start prometheus"))
        self.assertIn("trap 'docker start prometheus >/dev/null' EXIT", commands[0])

    def test_empty_prometheus_snapshot_fails(self):
        def save_empty_archive(command, destination):
            with tarfile.open(destination, "w"):
                pass

        with mock.patch.object(backup, "stream_remote", side_effect=save_empty_archive):
            with self.assertRaisesRegex(RuntimeError, "snapshot is empty"):
                backup.snapshot_prometheus(self.root)

    def fake_collect(self, stage):
        members = []
        for name in ("pgsql-db-000.dump", "pgsql-globals.sql",
                     "pgvector-db-000.dump", "pgvector-globals.sql",
                     "prometheus.tar"):
            (stage / name).write_bytes((name + "-test-content").encode())
            members.append({"file": name})
        return members

    def test_backup_is_encrypted_listed_and_verified(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        commands = []

        def list_databases(argv):
            self.assertIn(argv[4], ("pgsql", "pgvector"))
            commands.append(argv[4])
            return ("postgres\n" + argv[4] + "_app\n").encode()

        def stream(command, path):
            if path.name == "prometheus.tar":
                with tarfile.open(path, "w") as archive:
                    data = b"historical sample block"
                    info = tarfile.TarInfo("sample-block")
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            else:
                path.write_bytes((path.name + "-test-content").encode())

        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "password_file", return_value=self.password), \
             mock.patch.object(backup, "capture_remote", side_effect=list_databases), \
             mock.patch.object(backup, "stream_remote", side_effect=stream):
            backup.backup()
        self.assertEqual(commands, ["pgsql", "pgvector"])
        encrypted = list(directory.glob("backup-*.enc"))
        self.assertEqual(len(encrypted), 1)
        self.assertEqual(encrypted[0].stat().st_mode & 0o777, 0o600)
        self.assertEqual(encrypted[0].with_suffix(".json").stat().st_mode & 0o777, 0o600)
        self.assertTrue(encrypted[0].read_bytes().startswith(b"Salted__"))
        self.assertNotIn(b"pgsql-db-000", encrypted[0].read_bytes())
        backup.verify_set(encrypted[0], encrypted[0].with_suffix(".json"), self.password)
        target = self.root / "extracted"
        with mock.patch.object(backup, "password_file", return_value=self.password):
            backup.extract_set(directory, encrypted[0].stem, target)
            with self.assertRaisesRegex(ValueError, "already exists"):
                backup.extract_set(directory, encrypted[0].stem, target)
        self.assertTrue((target / "pgsql-db-000.dump").is_file())
        self.assertTrue((target / "pgvector-db-001.dump").is_file())
        self.assertTrue((target / "prometheus.tar").is_file())
        self.assertTrue((target / "manifest.json").is_file())
        self.assertFalse((target / ".incomplete").exists())
        self.assertFalse((directory / ".backup.lock").exists())

    def test_tampered_archive_fails_authentication(self):
        stage = self.root / "stage"
        stage.mkdir()
        members = self.fake_collect(stage)
        plain = self.root / "plain.tar.gz"
        encrypted = self.root / "backup.enc"
        metadata = self.root / "backup.json"
        backup.create_archive(stage, members, plain)
        metadata.write_text(json.dumps(backup.encrypt(plain, encrypted, self.password)))
        with encrypted.open("ab") as output:
            output.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            backup.verify_set(encrypted, metadata, self.password)

    def test_failed_collection_publishes_nothing(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "password_file", return_value=self.password), \
             mock.patch.object(backup, "collect", side_effect=RuntimeError("dump failed")):
            with self.assertRaisesRegex(RuntimeError, "dump failed"):
                backup.backup()
        self.assertEqual(list(directory.iterdir()), [])

    def test_failed_verification_publishes_nothing(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "password_file", return_value=self.password), \
             mock.patch.object(backup, "collect", side_effect=self.fake_collect), \
             mock.patch.object(backup, "verify_set", side_effect=ValueError("verification failed")):
            with self.assertRaisesRegex(ValueError, "verification failed"):
                backup.backup()
        self.assertEqual(list(directory.iterdir()), [])

    def test_backup_refuses_an_overlapping_run(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        (directory / ".backup.lock").mkdir(mode=0o700)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "password_file", return_value=self.password), \
             mock.patch.object(backup, "collect") as collect:
            with self.assertRaisesRegex(RuntimeError, "another backup is running"):
                backup.backup()
        collect.assert_not_called()

    def test_main_backup_uses_the_backup_path(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "run_backup") as run_backup, \
             mock.patch.object(sys, "argv", [str(SCRIPT), "backup"]):
            self.assertEqual(backup.main(), 0)
        run_backup.assert_called_once_with()

    def test_main_verify_uses_the_selected_backup_set(self):
        directory = self.root / "backups"
        name = "backup-20261111T020000Z-1234abcd"
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "password_file", return_value=self.password), \
             mock.patch.object(backup, "verify_set") as verify_set, \
             mock.patch.object(sys, "argv", [str(SCRIPT), "verify", name]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(backup.main(), 0)
        verify_set.assert_called_once_with(
            directory / f"{name}.enc", directory / f"{name}.json", self.password,
        )

    def test_retention_preview_uses_successful_calendar_periods(self):
        days = (
            "20261111", "20261110", "20261109", "20261108",
            "20261107", "20261106", "20261105", "20261104",
            "20261030", "20261023", "20261016", "20261009",
            "20260930", "20260831", "20260731",
        )
        names = [f"backup-{day}T020000Z-00000001" for day in days]
        names.append("backup-20261111T010000Z-00000002")
        keep, remove = backup.retention_plan(names)
        expected = {f"backup-{day}T020000Z-00000001" for day in (
            "20261111", "20261110", "20261109", "20261108",
            "20261107", "20261106", "20261105", "20261030",
            "20261023", "20260930",
        )}
        self.assertEqual(set(keep), expected)
        self.assertEqual(set(remove), set(names) - expected)
        self.assertIn("backup-20261111T010000Z-00000002", remove)

    def test_preview_ignores_incomplete_sets(self):
        directory = self.root / "backups"
        directory.mkdir()
        complete = "backup-20261111T020000Z-00000001"
        incomplete = "backup-20261110T020000Z-00000001"
        (directory / f"{complete}.enc").write_bytes(b"test")
        (directory / f"{complete}.json").write_text("{}")
        (directory / f"{incomplete}.json").write_text("{}")
        self.assertEqual(backup.complete_sets(directory), [complete])

    def test_prune_previews_then_removes_only_old_complete_sets(self):
        directory = self.root / "backups"
        directory.mkdir()
        stage = self.root / "stage"
        stage.mkdir()
        plain = self.root / "plain.tar.gz"
        backup.create_archive(stage, self.fake_collect(stage), plain)
        encrypted = self.root / "template.enc"
        metadata = json.dumps(backup.encrypt(plain, encrypted, self.password))
        names = [f"backup-20261111T0{hour}0000Z-00000001" for hour in (1, 2, 3)]
        for name in names:
            shutil.copyfile(encrypted, directory / f"{name}.enc")
            (directory / f"{name}.json").write_text(metadata)
        with mock.patch.object(backup, "password_file", return_value=self.password):
            with contextlib.redirect_stdout(io.StringIO()) as preview:
                backup.prune(directory, False)
            self.assertIn("host free:", preview.getvalue())
            self.assertEqual(len(backup.complete_sets(directory)), 3)
            with contextlib.redirect_stdout(io.StringIO()):
                backup.prune(directory, True)
        self.assertEqual(backup.complete_sets(directory), [names[-1]])
        self.assertFalse((directory / ".backup.lock").exists())

    def test_prune_keeps_older_sets_if_newest_is_damaged(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        stage = self.root / "stage"
        stage.mkdir()
        plain = self.root / "plain.tar.gz"
        backup.create_archive(stage, self.fake_collect(stage), plain)
        encrypted = self.root / "template.enc"
        metadata = json.dumps(backup.encrypt(plain, encrypted, self.password))
        older = "backup-20261111T010000Z-00000001"
        newest = "backup-20261111T020000Z-00000001"
        for name in (older, newest):
            shutil.copyfile(encrypted, directory / f"{name}.enc")
            (directory / f"{name}.json").write_text(metadata)
        with (directory / f"{newest}.enc").open("ab") as output:
            output.write(b"damaged")

        with mock.patch.object(backup, "password_file", return_value=self.password):
            with self.assertRaisesRegex(ValueError, "authentication failed"):
                backup.prune(directory, True)

        self.assertEqual(backup.complete_sets(directory), [older, newest])
        self.assertFalse((directory / ".backup.lock").exists())

    def test_prune_refuses_running_backup(self):
        directory = self.root / "backups"
        directory.mkdir()
        (directory / ".backup.lock").mkdir()
        with self.assertRaisesRegex(RuntimeError, "backup or prune is running"):
            backup.prune(directory, True)

    def test_run_status_tracks_success_then_failure_without_losing_last_success(self):
        directory = self.root / "backups"
        directory.mkdir(mode=0o700)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "backup", return_value="backup-20261111T020000Z-00000001"):
            backup.run_backup()
        path = directory / "backup-status.json"
        succeeded = json.loads(path.read_text())
        self.assertEqual(succeeded["last_run_outcome"], "success")
        self.assertEqual(succeeded["last_success_set"], "backup-20261111T020000Z-00000001")
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with mock.patch.object(backup, "backup_dir", return_value=directory), \
             mock.patch.object(backup, "backup", side_effect=RuntimeError("dump failed")):
            with self.assertRaisesRegex(RuntimeError, "dump failed"):
                backup.run_backup()
        failed = json.loads(path.read_text())
        self.assertEqual(failed["last_run_outcome"], "failure")
        self.assertEqual(failed["last_success_utc"], succeeded["last_success_utc"])
        self.assertEqual(failed["last_success_set"], succeeded["last_success_set"])
        self.assertNotIn("dump failed", path.read_text())


if __name__ == "__main__":
    unittest.main()
