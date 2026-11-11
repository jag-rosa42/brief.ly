# Health, team status, backups, and disaster recovery roadmap

## Goal and agreed scope

Give the team a reliable way to see whether the application is reachable,
detect failed or stale backups, and restore its data after an incident. Reuse
the Prometheus, Grafana, Pushgateway, and application metrics from
`feature/78-infra-implement-prometheus-grafana` as the starting point. Let that
branch's P2.2 dashboard and alerts finish before adapting deployment here.

The status page is an **internal Grafana view for the team**. No React status
page or new FastAPI status service is planned. Keep Prometheus, Pushgateway,
Blackbox Exporter, and every `/metrics` route internal. The existing Grafana
dashboard can serve as the status page after a clear gateway probe panel is
added; make a separate summary dashboard only if the completed dashboard is
too busy for a quick status check.

Run monitoring as a separate Compose project on the **same VM** so an
application-project `down` does not stop Grafana. This does not survive VM,
host, or Docker daemon failure. Off-VM monitoring is a later option if that
failure mode must be visible while the VM is down. Backups must leave the VM
and go to a configurable directory on its host.

## Ownership and integration boundary

- **Teammate on `feature/78`:** finish P2.2 through its integration checks,
  including the existing dashboard, data source, alerts, and observability
  documentation. Keep the Grafana data source URL
  `http://prometheus:9090`. No dashboard layout change is required for this
  roadmap.
- **This feature branch:** own the monitoring Compose split, shared-network
  setup, HTTP probe, status panel or optional summary dashboard, backup
  automation, recovery runbook, and new verification. Adapt documentation and
  Make targets after `feature/78` is integrated. Avoid simultaneous edits to
  its Grafana provisioning files and `roadmap.md`.
- **Integration:** merge or rebase the finished `feature/78` work before
  moving its monitoring services. Review the combined Compose configuration
  and preserve existing Prometheus, Grafana, and Pushgateway data volumes.
  Confirm the final metric names and Grafana provisioning paths from that
  branch rather than guessing them.

## 0. Agree on the recovery contract

- [ ] Confirm which environment is protected (local development VM, deployed
  VM, or both). Set `BACKUP_HOST_DIR` in the host's root `.env` to an absolute
  directory outside `VM_DIR`; document a safe example in `.env.example`.
  This is a path on the **host**, not a path inside the guest VM.
- [ ] Validate the agreed initial targets in a restore drill: daily backups,
  at most 24 hours of data loss (RPO), and service restoration within 4 hours
  (RTO). The 4-hour RTO remains a target until the timed drill proves it.
- [ ] Inventory data required for recovery: all application databases in
  `pgsql`, the AI database in `pgvector`, database roles, configuration needed
  to redeploy, and secrets that must be retained or deliberately rotated.
  Decide whether Grafana's mutable data is required; provisioned dashboards
  can be recreated from Git. Prometheus history is not required to restore
  the application.

**Check:** the chosen backup destination, retention, protected data, RPO, and
RTO are written down before automating deletion or retention.

## 1. Separate monitoring from the application lifecycle

- [ ] After `feature/78` is integrated, move its existing Prometheus, Grafana,
  and Pushgateway service definitions into a dedicated monitoring Compose
  project. Reuse their configuration, secrets, and persistent data; do not
  create duplicate monitoring instances.
- [ ] Create stable Docker networks independently of either Compose project.
  Attach Prometheus to the shared networks required to scrape the gateway,
  five FastAPI services, and Pushgateway. Keep Grafana and Pushgateway off the
  public application gateway. Declare shared networks `external` in both
  projects so application `down` cannot remove them.
- [ ] Give Grafana a team-only access path independent of Traefik, such as a
  loopback-bound port reached by SSH forwarding. Keep its administrator
  password in a secret file. Preserve the provisioned data source URL
  `http://prometheus:9090`.
- [ ] Add explicit commands and documentation for starting, stopping, and
  inspecting each project. Ensure application cleanup targets do not stop or
  delete monitoring containers or volumes.

**Check:** with both projects running, all existing Prometheus targets are
`UP`; after stopping only the application project, Grafana remains reachable
and reports the missing application targets. Restart the application and
confirm recovery without recreating monitoring data.

## 2. Probe the application and show team status

- [ ] Add Prometheus Blackbox Exporter to the monitoring project and configure
  an HTTP probe of the application's HTTPS entry point. Probe through the
  gateway, not a container-local API URL, so a gateway outage is visible.
  Handle the project's development certificate explicitly; do not silently
  disable TLS verification in a deployed environment.
- [ ] Configure Prometheus to scrape the exporter and the named probe target.
  Use bounded target labels. Distinguish `up` (Prometheus can scrape a target)
  from `probe_success` (the probed HTTP endpoint worked).
- [ ] Add a prominent gateway `probe_success` and last-check panel to the
  completed Grafana dashboard. Reuse its existing service availability
  panels. Show `unknown` or missing data distinctly from healthy.
- [ ] Add an alert for sustained probe failure. Keep existing API and worker
  alerts from P2.3, changing only what deployment integration requires.

**Check:** a normal HTTPS request yields `probe_success = 1`; stopping the
gateway yields `probe_success = 0` and a visible Grafana failure; restarting
it clears the alert. Grafana remains available when the application project
is stopped. Verify external requests cannot reach `/metrics`, Prometheus, or
Pushgateway.

## 3. Automate recoverable backups

- [ ] Implement a repeatable backup command that dumps every application
  database from `pgsql` and the AI database from `pgvector` using PostgreSQL
  custom-format archives, plus cluster globals/roles from each instance.
  Fail the run if any dump or upload fails; avoid treating a partially
  completed set as a successful backup.
- [ ] Run the backup from the **host**: use the project's existing SSH access
  to execute database dumps in the VM and transfer the completed archives to
  the host. The current QEMU setup does not mount a writable host directory
  inside the VM, so do not treat `BACKUP_HOST_DIR` as a guest path.
- [ ] Store the completed set in an encrypted Restic repository rooted at
  `BACKUP_HOST_DIR`. Validate that the variable is set to an absolute,
  writable host directory outside `VM_DIR` before starting; fail clearly
  instead of falling back to a directory inside the VM. Keep repository
  credentials out of Git and application images. Define retention only after
  the recovery contract is agreed. Do not copy a live PostgreSQL data
  directory as the database backup.
- [ ] Schedule the same host-side command independently of the application
  Compose lifecycle. Expose it as an explicit manual command (for example,
  `make backup`) and provide a way to list available backup snapshots.
  Prevent overlapping runs and keep actionable logs without printing secrets.
  Document that a sleeping or powered-off host cannot run its scheduled job.
- [ ] Publish a bounded last-success timestamp and last-run outcome for
  monitoring. Alert when a run fails or the most recent successful backup is
  older than the agreed interval. Check encrypted-repository integrity on a
  schedule.

**Check:** create test data in both database instances, run the manual backup
command, list the new snapshot, and confirm archives and globals can be read
from `BACKUP_HOST_DIR` on the host after stopping the VM. Change the variable
to another host directory and repeat. Force one dump or transfer failure and
verify the command fails and the alert can fire. Confirm the scheduled and
manual paths use the same backup logic.

## 4. Write and exercise disaster recovery

- [ ] Write a runbook for accidental data deletion, database corruption, and
  loss of the VM. Include prerequisites, retrieval of secrets, clean VM
  provisioning, database creation, restore order, application startup, and
  rollback or retry steps.
- [ ] Provide a manual restore command that accepts a chosen snapshot and
  reads it from the host's `BACKUP_HOST_DIR`, then restores it into a separate,
  disposable VM or database environment for evaluation. Make the target
  explicit and require confirmation before replacing any existing database.
  The host initiates SSH and sends the selected archives to the guest; the
  guest does not need an SSH server on the host or a host-directory mount.
  Do not make the demonstration depend on damaging live data.
- [ ] Restore the latest backup into a clean environment with matching
  PostgreSQL and pgvector support. Verify database roles, schema, representative
  records from **both** instances, and critical application requests.
- [ ] Record backup age, actual data loss, restore time, commands used, and
  gaps found in the drill. Update the runbook and targets based on evidence.

**Check:** during a repeatable demonstration, create identifiable data in
both database instances, run a manual backup, list and select its snapshot,
restore into the disposable environment, and query the restored data. Another
teammate can follow the runbook without relying on the original VM's volumes.
The timed drill meets the agreed RPO and RTO, or documents why it does not.

## Definition of done

- [ ] The finished `feature/78` dashboards and alerts still work after the
  Compose split, and monitoring survives application-project `down`.
- [ ] The Grafana status view shows gateway reachability, internal service
  availability, and backup freshness without exposing internal metrics.
- [ ] Automated backups of both PostgreSQL instances exist off-VM and produce
  observable success/failure signals. The destination is configurable with
  `BACKUP_HOST_DIR` and remains accessible after the VM is stopped.
- [ ] A teammate can demonstrate manual backup, snapshot listing, and manual
  restore of both databases without modifying the running application data.
- [ ] A clean restore drill passes and the disaster recovery runbook reflects
  the steps actually tested.

Do not mark a checkbox complete until its stated check passes.
