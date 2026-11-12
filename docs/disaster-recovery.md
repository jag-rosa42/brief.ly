# Disaster recovery contract and inventory

This document records what must be available to rebuild the application after
loss of its VM. The initial target is one backup per day, at most 24 hours of
data loss (RPO), and restoration within 4 hours (RTO). The RTO is a target
until a timed restore drill demonstrates it.

## Backup location and retention

- The protected environment is the project VM. Backups must be stored on its
  **host**, outside `VM_DIR`, in the absolute directory named by
  `BACKUP_HOST_DIR` in the host's root `.env`. This is a host path, not a path
  inside the guest. The completed encrypted backup sets must remain
  accessible after the VM stops.
- The host `.env` sets `PROJECT_STORAGE_DIR` (the project directory by default)
  and explicitly derives `VM_DIR` and `BACKUP_HOST_DIR` beneath
  it. Git and `vm-sync` exclude these directories. Changing the storage root
  changes the configured paths but does not move existing disks or backup sets;
  move or retain them deliberately, then reinstall the backup schedule so its
  log points to the new backup directory.
- **Retention:** keep one completed backup set from each of the latest 7 days,
  4 weeks, and 3 months with successful runs. A set can satisfy more than one
  period. Each set must contain the database dumps, cluster globals, and a
  consistent Prometheus TSDB snapshot from the same run. Missing scheduled
  runs do not create restore points. Measure backup size and available host
  space before enabling deletion; delete old sets only after the new set has
  been encrypted and verified.

  For example, if two backups succeed on the same UTC date, the newest can
  cover that day's daily, weekly, and monthly slots. The older same-day set
  becomes a removal candidate. If a day has no successful backup, the rule
  looks farther back for the seventh successful date; it does not invent a
  missing restore point.
- The host-side backup script uses tools already installed on the host,
  including SSH, archive utilities, checksums, and OpenSSL. It must require a
  separately stored encryption password, fail if encryption or verification
  fails, and never log the password. The encrypted backup sets remain outside
  Git, application images, and the VM. OpenSSL encrypts the compressed tar
  archive with AES-256-CBC and PBKDF2; a separate HMAC authenticates its
  ciphertext before decryption. The backup command verifies the encrypted
  archive and each archived member before publishing the set.

### Manual backup on the host

Run the host-only generation target once, and keep a separate protected copy
of the password for disaster recovery. `make secrets` also runs this target;
it preserves an existing password. The script refuses an empty or non-private
file. Do not run these commands inside the VM:

```sh
make secrets-backup-password
make backup
make backup-list
make backup-retention-preview
make backup-prune
backup_set=backup-YYYYMMDDTHHMMSSZ-XXXXXXXX  # Replace with a name from backup-list.
make backup-verify BACKUP_SET="$backup_set"
make backup-extract BACKUP_SET="$backup_set"
```

The host's `.env` sets `BACKUP_PASSWORD_FILE` to
`$(CURDIR)/shared/secrets/backup_password`; it contains a path, not the
password. Git ignores `shared/secrets`, and `vm-sync` excludes this one file
so the backup password stays on the host. The script also reads
`BACKUP_HOST_DIR`, `VM_DIR`, `VM_SSH_PORT`, and `POSTGRES_USER` from `.env`.
It connects to the VM through the existing SSH port,
dumps every non-template database and cluster globals from `pgsql` and
`pgvector`, then stops Prometheus briefly while copying its TSDB. It restarts
Prometheus even if copying fails. If Prometheus has not yet been integrated,
`make backup` fails without publishing a completed set. The backup set is an
encrypted `.enc` file with a small authentication `.json` sidecar; both are
needed to verify and restore it. `make backup-extract` verifies and decrypts a
chosen set into a **new** host directory with private permissions. It refuses
an existing destination and never changes the running VM or databases. The
default destination is `$(CURDIR)/backup-extract-<backup-set>` on the host;
override it with `TARGET_DIR=/absolute/new/directory` when needed. Git and
`vm-sync` exclude the default directory pattern. The
extracted files are plaintext; protect the destination and remove it when the
drill is over. If extraction fails, a `.incomplete` marker remains in the
destination. `make backup-restore BACKUP_SET=<set>` verifies a set, asks before
recreating the configured VM, and loads the databases and Prometheus history
into that fresh guest before starting the full stack.
`make backup-retention-preview` reads the dates of
completed sets and prints `KEEP` or `WOULD REMOVE` without deleting files.
It chooses the newest set in each of the latest 7 UTC dates, 4 ISO calendar
weeks, and 3 calendar months that contain a successful run. Multiple backups
on the same day may therefore leave older same-day sets as removal candidates.
`make backup-prune` verifies the newest set, reports completed-set sizes and
free host space, and previews removal. After checking the report and available
space, `make backup-prune APPLY=1` removes only the older complete sets that
are outside the retention rule. Pruning does not run automatically after a
backup; it is an explicit host operation until the scheduled workflow has
been tested.

### Preparing a host schedule

Run `make backup-schedule-install BACKUP_TIME=1234` on the **host** to install
one daily 12:34 cron entry. `BACKUP_TIME` is exactly four digits in 24-hour
`HHMM` format; for example, `0203` means 02:03 and `2305` means 23:05.
Omitting it uses `0200` (02:00). Invalid hours or minutes are rejected. The
entry calls the same `make backup` command used manually; the
installer preserves unrelated cron jobs and replaces its own marked entry on
repeat runs. Inspect the installed entry with `crontab -l`. It writes a private
log to `BACKUP_HOST_DIR/backup.log`.

Every `make backup` run atomically writes `BACKUP_HOST_DIR/backup-status.json`
with the last run time, outcome, last success time, and completed set name. The
file contains no password or dump contents. A failure leaves the previous
last-success value in place and exits nonzero, so the scheduler can report the
error. A sleeping or powered-off host cannot run its scheduled command at
the chosen time; a missed run must be detected from the last-success time.

The status file keeps the previous success when a later run fails. For
example, this records a failed run on November 12 while the last verified set
is still from November 11:

```json
{
  "last_run_utc": "2026-11-12T02:00:00+00:00",
  "last_run_outcome": "failure",
  "last_success_utc": "2026-11-11T02:00:00+00:00",
  "last_success_set": "backup-20261111T020000Z-1234abcd"
}
```

The installed cron entry uses absolute paths for Make, the project, and the
log, and supplies a `PATH` containing the required host tools. Its five time
fields mean minute, hour, every day, every month, and every weekday.
A log and status file are useful only if someone checks for failures and stale
`last_success_utc` values.

## Data needed for recovery

| Source | What to preserve | How to check the inventory |
| --- | --- | --- |
| `pgsql` (PostgreSQL 18) | All non-template databases, currently `identity_db`, `personalization_db`, `content_management_db`, and `morning_briefing_db`; cluster globals/roles and permissions | Compare the database list from the running `pgsql` instance with the backup manifest. Include any database added later, rather than relying only on this list. |
| `pgvector` (PostgreSQL 18 with pgvector) | All non-template databases, currently `ai_processing_db`; cluster globals/roles and permissions | Compare the database list from the running `pgvector` instance with the backup manifest. The restore target must have compatible pgvector support. |
| Prometheus history (after integration) | The retained time-series data in Prometheus's `prometheus_data` volume | Create a consistent TSDB snapshot, transfer it to the host, and include it in the same encrypted backup set as the databases. Verify a restored Prometheus can query data from before the backup. Never copy the live data directory while Prometheus is writing. |
| Versioned deployment files | The Git commit containing `compose.yaml`, its overrides, Makefiles, VM provisioning, gateway configuration, database migrations, and (after integration) Grafana and Prometheus provisioning | Record the deployed commit with each backup or restore drill. Recover these files from Git at that revision. |
| Unversioned configuration | Root `.env` and the five `srcs/services/*/.env` files, plus the host's VM SSH access details | Keep a protected operator copy outside Git and the VM. The `.env.example` files document names and defaults but may not reproduce actual deployed settings. |
| Application secrets | `shared/secrets/postgres_password`, `jwt_private_key`, `jwt_public_key`, `news_api_key`, `certs/localhost.pem`, `certs/localhost-key.pem`, `services/personalization_client_secret`, `services/morning_briefing_client_secret`, and `services/ai_processing_client_secret` | Keep a protected operator copy outside Git and the VM. Check that each file needed by Compose exists before starting the restored stack; never put its contents in a backup log or manifest. |
| Monitoring access (after integration) | Grafana administrator password secret and configured administrator username | Restore or rotate these to regain team access to the provisioned Grafana view. Local Grafana users are not preserved. |
| Backup access | Encryption password and host access to `BACKUP_HOST_DIR` | Keep independent protected copies outside Git and the VM. Without the password, the encrypted backup sets cannot be recovered. |

The PostgreSQL password must match the restored roles and application
configuration. Rotating the JWT key invalidates existing tokens; rotating
service client secrets or provider credentials requires updating the services.
For a fresh VM, the development TLS certificate can be recreated; a deployed
certificate needs its own renewal or replacement procedure.

**Monitoring decision:** the provisioned Grafana dashboards, alerts, and data
sources in Git are sufficient for recovery after the monitoring branch is
integrated. Mutable Grafana data, including UI-only changes and local users,
is outside this recovery contract. Make dashboard and alert changes in
provisioning files so they can be recreated. Prometheus history **is** in
scope: restore the retained TSDB data into the monitoring project before
starting Prometheus. The source branch currently limits its retained history
to 15 days or 2 GB, whichever applies first; a backup cannot recover data
already deleted by that policy. Recheck these limits after integration.

## Contract check before backup automation

Confirm the host destination, retention, and complete data inventory. Then
perform a backup and restore drill for both PostgreSQL instances and the
Prometheus TSDB. Record the backup age, elapsed restore time, and oldest
queryable restored metric, then compare them with the RPO and RTO above.

## Recovery runbook: recreate the configured VM

Use this path when the current VM is lost or its databases must be replaced.
It is an **in-place recovery**: the confirming `make create-vm` step deletes
`VM_DIR`'s guest disk, including its Docker volumes. The encrypted backup and
its password stay on the host, outside `VM_DIR`. Do not start if the backup,
password, `.env`, or application secrets are missing. If the old VM still
runs, stop application writes and preserve any incident evidence first.

For accidental deletion or corruption, select a set completed **before** the
event. For VM loss, select the newest verified set. Every change after the
selected backup's timestamp will be absent from the restored VM.

### 1. Verify a host backup

From the repository root on the host, check the storage paths in `.env`, then
choose and verify a completed set. `backup-restore` also verifies it before
showing the deletion prompt:

```sh
make backup-list
backup_set=backup-YYYYMMDDTHHMMSSZ-XXXXXXXX  # Replace with a listed set.
make backup-verify BACKUP_SET="$backup_set"
```

Keep independent copies of the root and service `.env` files, SSH key,
application and Grafana secrets, and `BACKUP_PASSWORD_FILE`. Use the Git
revision in the set's `manifest.json`; the recorded commit does not include
uncommitted deployment changes. The host needs enough space for a fresh VM
and temporary decrypted archives. The restored guest needs the same
PostgreSQL 18 and pgvector `pg18` support as the backup.

### 2. Recreate, restore, and start

```sh
make backup-restore BACKUP_SET="$backup_set"
```

The command verifies the set, prints the exact `VM_DIR` that will be replaced,
and asks for confirmation. Declining stops the command. On confirmation it
stops and recreates only that VM, waits for cloud-init, syncs the project,
starts empty `pgsql` and `pgvector` containers, restores their roles and all
non-template databases, and copies the Prometheus snapshot into a stopped
container. It then starts the application and monitoring stack in the guest.
The script checks that the configured SSH port owns the new QEMU
disk and that the databases and Prometheus volume are empty before importing.
Do not rerun it after a partial restore without choosing to recreate the VM
again. If cloud-init reports recoverable errors, confirm `docker version`
works in the guest before retrying.

For a production port-forwarding layout, pass `VM_NETWORK_MODE=prod` to the
command; otherwise it uses the configured Make value (dev by default). QEMU
fixes forwarded ports when the VM starts, so changing modes later requires a
restart.

### 3. Check the recovered application

`backup-restore` starts both Compose projects. Connect to the restored guest
to verify the application and monitoring. The monitoring project remains
separate from the application project:

```sh
make connect-vm
```

Inside that same guest, compare the restored database lists, roles, schemas,
and representative records with the backup manifest. For the 2026-11-12 drill
set, these return one marker from each PostgreSQL instance:

```sh
docker exec -u postgres pgsql psql -U transcendence -d restore_drill_20261112 -Atqc 'SELECT instance, marker FROM restore_marker'
docker exec -u postgres pgvector psql -U transcendence -d restore_drill_20261112 -Atqc 'SELECT instance, marker FROM restore_marker'
```

Check a historical Prometheus sample using a UTC time **before** the backup;
Prometheus stays internal. Check the five backend `/health` endpoints from
inside their containers and the HTTPS gateway with the project's development
certificate. The host's Grafana URL is `http://127.0.0.1:${GRAFANA_PORT}/login`
with the configured port (3000 by default). Do not expose Prometheus,
Pushgateway, or `/metrics` through the gateway.

```sh
docker exec prometheus wget -qO- 'http://127.0.0.1:9090/api/v1/query?query=up&time=<UTC-before-backup>'
for service in identity personalization morning-briefing content-management ai-processing; do
  docker exec "$service" python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/health").status)' || break
done
curl --silent --show-error --cacert shared/secrets/certs/localhost.pem --output /dev/null --write-out '%{http_code}\n' https://localhost:8443/
exit
```

Run representative authenticated identity, content, personalization, morning
briefing, and AI requests as applicable. Record expected rows and response
codes. The gateway request and health checks alone do not prove all user flows.

### 4. Record the outcome and retry if needed

Record the selected set and its Git commit, backup time, incident or test-write
time, restore start and end times, historical metric time, database rows, and
application requests checked. Compare observed data loss with the 24-hour RPO
and elapsed recovery with the 4-hour RTO. An untimed run cannot prove RTO.
If verification fails, keep the encrypted set and investigate the failure;
choose another verified set if needed, then run `make backup-restore` again to
recreate a fresh guest. Do not route real traffic until the recovered
application and data are accepted.

### Drill record: 2026-11-12 (in progress)

- The host created and verified
  `backup-20261112T102237Z-10e7b837` at 10:22:37 UTC. A dedicated
  `restore_drill_20261112` database held one non-sensitive marker row in
  **each** source PostgreSQL instance before backup.
- The restore VM was recreated with a separate disk and SSH port 2223. Both
  restored instances returned the expected marker (`pgsql` and `pgvector`),
  and `content_management_db.sources` contained seven rows. The restore
  command also loaded the Prometheus snapshot into its own stopped container.
- An earlier drill with `backup-20261112T063324Z-318b2c0c` returned 15
  historical Prometheus `up` series at 06:30 UTC, five backend health 200s,
  HTTPS gateway 200, and a live gateway probe value of 1. That earlier set
  lacked pgvector application rows, which prompted the two marker databases.
- **Still to check for the new set:** historical Prometheus query, Grafana
  access, application requests, and a measured restore duration. No incident
  data-loss or RTO result is claimed from this drill. The source marker
  databases remain in place for inspection; remove them only as a separate,
  deliberate cleanup step.
