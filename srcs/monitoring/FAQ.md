## Feature 229 decision memo: status, backups, and recovery

This section records the team's choices from the planning discussion. It is a
**plan**, not a claim that the work below has already been implemented. See
the feature 229 `roadmap.md` for ordered tasks and acceptance checks. The FAQ
above comes from `feature/78-infra-implement-prometheus-grafana` and explains
that branch's monitoring concepts.

### Will the status page be in Grafana, React, or FastAPI?

It will be an **internal Grafana view for the team**. We do not need a new
React page or a FastAPI status service. The existing P2.2 Grafana dashboard
can serve as the status page after we add a clear gateway reachability panel.
If that dashboard proves too detailed for a quick check, we can make a small
summary dashboard later.

### What happens to the status page if the application stack is stopped?

Grafana cannot remain available if it is stopped with the same Compose
project. After feature 78 is integrated, we plan to move its **existing**
Grafana, Prometheus, and Pushgateway services into a separate monitoring
Compose project on the same VM. Application-project `down` will then leave
monitoring running. We are changing deployment ownership, not creating a
second Grafana or Prometheus installation.

This protects the status view from an **application Compose outage**. It does
not protect it from a VM, host, or Docker daemon outage. Monitoring would need
another host to remain visible during those failures.

### How can Prometheus scrape services in another Compose project?

Both projects will join shared Docker networks created independently of
either project and declared `external` in Compose. Prometheus can still reach
API targets such as `identity:8000` and Traefik on those networks. Grafana
will continue to reach Prometheus at `http://prometheus:9090`. Internal
`/metrics` routes and Pushgateway must not be published to users.

### What is an HTTP probe, and what does Blackbox Exporter add?

A probe is a repeated check of a target. The existing FastAPI `/health`
checks test a service and its database from inside the stack. Prometheus
Blackbox Exporter will make an HTTP request through the application's HTTPS
gateway and report `probe_success`: `1` when the request works, `0` when it
fails. This checks reachability from outside the application containers, so
it can reveal a gateway failure even when an API's internal health check is
fine. Prometheus scrapes the exporter; Grafana displays the resulting metric.
Prometheus `up` means a metrics target was scraped, which is a different
question from whether the HTTP probe succeeded.

### Does our teammate need to redesign his feature 78 dashboard?

No. He can finish P2.2 through the end of his roadmap as planned, including
dashboard provisioning and alerts. Feature 229 will integrate that work,
then add the gateway probe panel and backup freshness status. The main
integration changes concern Compose, networks, Make commands, and deployment
documentation. Confirm his final metric names and provisioning paths before
editing the dashboard. Avoid simultaneous changes to his Grafana files.

### Should this be orchestrated by Kubernetes instead of Compose?

The project currently deploys on one VM with Compose, so this roadmap keeps
Compose. Kubernetes can manage probes and restarts, but a single-node cluster
would still fail with its VM and would not replace off-VM backups or restore
drills. A multi-node Kubernetes migration is a separate platform decision.

### What are RPO and RTO, and what did we choose?

**RPO** is the maximum acceptable age of restored data. **RTO** is the target
time to restore service. We agreed on daily backups, a **24-hour RPO**, and
a proposed **4-hour RTO**. The four-hour target must be tested with a timed
clean restore; it is not yet a demonstrated guarantee. Companies choose these
targets according to service importance, data-loss tolerance, cost, and the
results of restore drills. There is no one universal company standard.

### Where will backups go, and how can I change the directory?

Set `BACKUP_HOST_DIR` in the root `.env` on the **host** to an absolute path
outside `VM_DIR`. The planned host-side backup command will store encrypted
backup snapshots there. Changing this variable will change the destination
without editing scripts. The command must fail clearly if it is missing or
points inside the VM disk directory. A directory on the host survives loss
of the VM, but not loss of that host's disk.

### What is a PostgreSQL cluster, and why dump its globals separately?

In PostgreSQL, a **cluster** is one server instance that manages one or more
databases. It does not mean a Kubernetes cluster. This project has two separate
PostgreSQL clusters: the `pgsql` container and the `pgvector` container.

A **role** is a PostgreSQL identity used for login, ownership, or permissions.
Roles belong to the whole cluster, so several databases can use the same role.
For example, a table in `identity_db` may be owned by the `transcendence` role.

`pg_dump -Fc identity_db` saves that database's schema and data. It can record
that the table belongs to `transcendence`, but it does not create the role:
the role is shared across the cluster rather than stored inside `identity_db`.
Restoring the database into a fresh server without that role can therefore
fail to restore ownership or permissions.

**Dumping cluster globals** means saving shared objects, including roles and
tablespaces, with `pg_dumpall --globals-only`. We save globals once from
`pgsql` and once from `pgvector`. During recovery, restore each cluster's
globals before its individual database dumps.

### Does the globals dump save who owns each table?

The database dump records that a particular table belongs to a role such as
`transcendence`. The globals dump defines that role for the whole PostgreSQL
instance. The backup script collects database dumps before globals; their
collection order does not matter. During a restore, create the roles from the
globals dump first, then restore the databases so their recorded owners exist.

### Which command saves the rows in a table?

`pg_dump -Fc -U transcendence -d identity_db` saves the database's schema and
the rows visible in its snapshot. `-Fc` selects PostgreSQL's custom archive
format. The script runs this command inside the `pgsql` or `pgvector` container
for every database and writes its output to a `.dump` file on the host.
`pg_dumpall --globals-only` saves shared roles and tablespaces, not table rows.

### How is a database dump saved and restored?

For `identity_db`, the host connects to the VM over SSH and runs `pg_dump`
inside the `pgsql` container. The dump bytes travel through SSH's output
stream into a host file such as `pgsql-db-000.dump`. The script packages that
file with the other dumps, globals, and Prometheus data, then encrypts and
verifies the backup set.

To restore, decrypt a chosen set on the host, create the required roles and an
empty target database in a separate recovery environment, and feed the `.dump`
file to `pg_restore`. It rebuilds the database objects and loads their saved
rows. The project has not yet implemented or demonstrated this restore command.

### Is the backup compressed with a password?

The script first packs the database dumps, cluster globals, and Prometheus data
into a compressed `.tar.gz` archive. It then encrypts that archive with the
password in `shared/secrets/backup_password`, producing a `.enc` file. Compression
makes the data smaller; encryption protects its contents.

The accompanying `.json` file contains authentication data used to detect
changes to the encrypted file, not the password. Both files and the password
are needed to verify and extract the backup. The temporary unencrypted archive
is removed after a successful run.

### What exactly does `pg_dump` capture if the database is changing?

`pg_dump` takes a consistent snapshot of one database. It saves its table
definitions, ownership and permission information, and rows visible at that
snapshot. For example, if `users` contains Alice and Bob at snapshot time,
both rows are saved. If Charlie is inserted afterward, Charlie is not in that
dump, even though the live database continues accepting writes. Each database
is dumped separately, so the two PostgreSQL instances do not share one exact
snapshot time.

### Will I be able to demonstrate manual backup and restore?

Yes. The plan requires a manual backup command, a way to list and choose
snapshots, and a manual restore command. The scheduled backup must use the
same logic as the manual command. For evaluation, restore the chosen snapshot
into a separate disposable environment, then query recognizable records in
both the regular PostgreSQL and pgvector databases. Do not overwrite live
application data just to demonstrate recovery.

### How will a VM restore read the host's backup directory?

The **host initiates SSH** using the project's existing host-to-VM connection.
The restore command reads the selected snapshot from `BACKUP_HOST_DIR`, sends
its archives to a clean or disposable VM, runs the database restore there,
and verifies the result. The VM does not need a writable host-directory mount
or an SSH server running on the host. If the original VM has been lost, a new
VM must be provisioned before this transfer and restore can run.

### What remains to decide or prove?

Choose a real host directory with enough space, agree on backup retention and
which secrets must be recoverable, then build and test the commands. Confirm
that scheduled backups can run while the host is awake, that failed or stale
backups alert the team, and that a clean restore meets the agreed targets.
