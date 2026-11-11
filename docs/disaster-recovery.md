# Disaster recovery contract and inventory

This document records what must be available to rebuild the application after
loss of its VM. The initial target is one backup per day, at most 24 hours of
data loss (RPO), and restoration within 4 hours (RTO). The RTO is a target
until a timed restore drill demonstrates it.

## Backup location and retention

- The protected environment is the project VM. Backups must be stored on its
  **host**, outside `VM_DIR`, in the absolute directory named by
  `BACKUP_HOST_DIR` in the host's root `.env`. This is a host path, not a path
  inside the guest. The directory and its Restic repository must remain
  accessible after the VM stops.
- The `.env.example` default is `$(CURDIR)/backups`, a host directory beneath
  the project root. Git and `vm-sync` exclude it. Confirm the actual host
  `.env` setting before the first backup drill; the example does not update an
  existing `.env` automatically.
- **Retention: undecided.** Agree how many daily, weekly, and monthly
  snapshots to keep before implementing any `restic forget --prune` schedule.
  No automated deletion should be configured until then.

## Data needed for recovery

| Source | What to preserve | Why |
| --- | --- | --- |
| `pgsql` (PostgreSQL 18) | Every non-template database, including `identity_db`, `personalization_db`, `content_management_db`, and `morning_briefing_db`; cluster globals and roles | Restores application records and the owners/permissions needed by the databases. Enumerate the live cluster at backup time so later databases are included. |
| `pgvector` (PostgreSQL 18 with pgvector) | Every non-template database, including `ai_processing_db`; cluster globals and roles | Restores AI data and its roles. The restore environment must have compatible pgvector support. |
| Deployment configuration | Git revision, Compose files, root and service `.env` values, VM provisioning and host SSH access details | Recreates the same images, database names, ports, and service connections. Keep environment values in a protected operator location, outside Git. |
| Application secrets | PostgreSQL password, JWT private key, service client secrets, provider credentials, and TLS private key/certificate under `shared/secrets/` | A restore needs working credentials. Retain them securely outside Git, or plan rotation and its effects before recovery. The public JWT key can be derived from the private key. |
| Backup credentials | Restic repository password and any key material used to access the host backup directory | Without these, encrypted snapshots cannot be restored. Keep a separate, protected copy outside the VM and Git. |

The PostgreSQL password must match the restored roles and application
configuration. Rotating the JWT key invalidates existing tokens; rotating
service client secrets or provider credentials requires updating the services.
For a fresh VM, the development TLS certificate can be recreated; a deployed
certificate needs its own renewal or replacement procedure.

Provisioned Grafana dashboards and data sources can be recreated from Git
after the monitoring branch is integrated. Prometheus history is not required
for application recovery. **Decision pending:** whether manually changed
Grafana dashboards, users, or other mutable Grafana data must be restored. If
so, add its persistent volume and credentials to the backup scope.

## Contract check before backup automation

Confirm the host destination, retention, complete data inventory, and the
Grafana decision. Then perform a backup and restore drill for both PostgreSQL
instances, record the backup age and elapsed restore time, and compare them
with the RPO and RTO above.
