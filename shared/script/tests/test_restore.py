"""Safety and ordering checks for both VM restore modes."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "restore.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("host_restore", SCRIPT)
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class RestoreTests(unittest.TestCase):
    def test_source_ssh_port_is_rejected(self):
        with mock.patch.object(restore.backup, "setting", return_value="2222"):
            with self.assertRaisesRegex(ValueError, "different SSH port"):
                restore.target_port("2222")
        with self.assertRaisesRegex(ValueError, "TCP port"):
            restore.target_port("not-a-port")

    def test_in_place_mode_requires_configured_vm_and_port(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "vm"
            other = Path(temp) / "other"
            source.mkdir()
            other.mkdir()
            settings = {"VM_DIR": str(source), "VM_SSH_PORT": "2222"}
            with mock.patch.object(restore.backup, "setting",
                                   side_effect=lambda name, default=None: settings[name]):
                self.assertEqual(restore.target_port("2222", in_place=True), 2222)
                with self.assertRaisesRegex(ValueError, "configured VM SSH port"):
                    restore.target_port("2223", in_place=True)
                with self.assertRaisesRegex(ValueError, "configured VM_DIR"):
                    restore.validate_target_vm(str(other), 2222, in_place=True)

    def test_existing_database_or_tsdb_is_rejected_before_restore(self):
        members = [
            {"instance": "pgsql", "database": "postgres"},
            {"instance": "pgvector", "database": "postgres"},
            {"kind": "prometheus-tsdb", "file": "prometheus.tar"},
        ]
        with mock.patch.object(restore, "remote", return_value="postgres\nidentity_db\n"):
            with self.assertRaisesRegex(ValueError, "not empty"):
                restore.preflight(2223, "/home/student/ft_transcendance", members,
                                  "transcendence", "example")

    def test_bootstrap_role_creation_is_skipped_but_alter_is_kept(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "globals.sql"
            prepared = Path(temp) / "prepared.sql"
            source.write_text("CREATE ROLE transcendence;\nALTER ROLE transcendence WITH SUPERUSER;\n")
            restore.globals_for_bootstrap(source, "transcendence", prepared)
            self.assertEqual(prepared.read_text(),
                             "ALTER ROLE transcendence WITH SUPERUSER;\n")

    def test_roles_restore_before_database_dumps(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for instance in ("pgsql", "pgvector"):
                (directory / f"{instance}-globals.sql").write_text(
                    "CREATE ROLE transcendence;\nALTER ROLE transcendence WITH SUPERUSER;\n")
                (directory / f"{instance}-postgres.dump").write_bytes(b"dump")
            members = [
                {"instance": instance, "kind": "globals", "file": f"{instance}-globals.sql"}
                for instance in ("pgsql", "pgvector")
            ] + [
                {"instance": instance, "database": "postgres", "file": f"{instance}-postgres.dump"}
                for instance in ("pgsql", "pgvector")
            ]
            with mock.patch.object(restore, "remote") as remote:
                restore.restore_databases(2223, directory, members, "transcendence")
            commands = [call.args[1] for call in remote.call_args_list]
            for instance in ("pgsql", "pgvector"):
                indices = [i for i, command in enumerate(commands) if instance in command]
                self.assertIn("psql", commands[indices[0]])
                self.assertIn("pg_restore", commands[indices[1]])


if __name__ == "__main__":
    unittest.main()
