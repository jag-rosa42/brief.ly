# Host-side backup and recovery commands. The Python script reads the host's
# root .env; none of these targets should be forwarded into the guest VM.

TARGET_DIR ?= $(CURDIR)/backup-extract-$(BACKUP_SET)
BACKUP_TIME ?= 0200

.PHONY: backup backup-schedule-install backup-list backup-retention-preview backup-prune backup-verify backup-extract backup-restore

backup:
	@python3 shared/script/backup.py backup

backup-schedule-install:
	@python3 shared/script/install_backup_cron.py --time "$(BACKUP_TIME)"

backup-list:
	@python3 shared/script/backup.py list

backup-retention-preview:
	@python3 shared/script/backup.py retention-preview

backup-prune:
	@python3 shared/script/backup.py prune $(if $(filter 1,$(APPLY)),--apply,)

backup-verify:
	@test -n "$(BACKUP_SET)" || { printf 'Set BACKUP_SET from make backup-list.\n' >&2; exit 1; }
	@python3 shared/script/backup.py verify "$(BACKUP_SET)"

backup-extract:
	@test -n "$(BACKUP_SET)" || { printf 'Set BACKUP_SET from make backup-list.\n' >&2; exit 1; }
	@test -n "$(TARGET_DIR)" || { printf 'Set TARGET_DIR to a new absolute host directory.\n' >&2; exit 1; }
	@python3 shared/script/backup.py extract "$(BACKUP_SET)" "$(TARGET_DIR)"

# Verify before asking to replace the configured VM. create-vm asks for
# confirmation and stops on cancellation; restore.py then requires empty
# databases and a missing Prometheus volume before importing anything.
backup-restore: backup-verify
	@make --no-print-directory create-vm VM_DIR="$(VM_DIR)" VM_SSH_PORT="$(VM_SSH_PORT)" VM_NETWORK_MODE="$(VM_NETWORK_MODE)"
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && make shared-networks && VM_GUEST_BIND_ADDRESS=0.0.0.0 docker compose -f compose.yaml --profile databases up -d --wait pgsql pgvector'
	@python3 shared/script/restore.py "$(BACKUP_SET)" --remote-dir "$(VM_REMOTE_DIR)"
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && VM_GUEST_BIND_ADDRESS=0.0.0.0 make docker SECRETS_MODE=validate SERVICE='
