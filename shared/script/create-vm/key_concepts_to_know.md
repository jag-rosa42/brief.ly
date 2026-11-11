# Key concepts: our QEMU VM and cloud-init setup

This guide explains the development VM created by `shared/script/create-vm.sh`. The goal is
not to memorize every command. It is to understand the system well enough to
operate it, diagnose it, and change it safely.

## The big picture

```text
Host computer
  └─ QEMU: supplies virtual hardware
       ├─ KVM (Linux) or HVF (macOS): fast CPU virtualization
       ├─ Ubuntu cloud-image disk: operating system and persistent files
       ├─ cloud-init seed disk: first-boot configuration
       └─ user-mode NAT: host SSH port → guest port 22
```

QEMU is the program that runs the virtual machine (VM). KVM is the Linux
kernel feature that lets QEMU execute a Linux guest efficiently on the host
CPU. On Apple Silicon macOS, the corresponding accelerator is HVF
(Hypervisor.framework).

The script chooses an Ubuntu image with the same CPU architecture as the host:

- Intel/AMD host: AMD64 image and `qemu-system-x86_64`.
- Apple Silicon/ARM host: ARM64 image and `qemu-system-aarch64`.

Using the native architecture matters: an ARM guest on an ARM host can be
accelerated; an AMD64 guest on Apple Silicon would need slow CPU emulation.

## What happens when we run `make launch-vm`

1. The script validates its inputs: CPU/RAM values, SSH port, username, and
   SSH public key.
2. It downloads a pinned official Ubuntu cloud image if it is not cached, and
   verifies it against Ubuntu's published SHA-256 checksum.
3. It creates a writable QCOW2 disk from that base image and expands its
   virtual capacity.
4. It writes cloud-init `user-data` and `meta-data` files for this developer.
5. QEMU starts Ubuntu with the operating-system disk, the cloud-init seed
   disk, UEFI firmware, virtual network hardware, and SSH port forwarding.
6. On the first boot, cloud-init creates the user, installs the SSH key and
   Docker, then enables Docker.

The first boot can take a few minutes because packages are downloaded and
installed.

## Important storage terms

### Cloud image

An Ubuntu cloud image is a preinstalled minimal Ubuntu system intended to be
configured automatically at first boot. It is not an installer ISO and does
not ask the usual interactive installation questions.

The downloaded image under `vm/images/` is a reusable base. Do not treat it as
our working VM disk.

### QCOW2 disk

`qcow2` is a QEMU virtual-disk format. Our writable VM disk is under `vm/` and
contains the VM's OS changes, source files, Docker images, and databases.

The disk is sparse: a disk configured as `50G` has a *maximum virtual size* of
50 GiB but does not necessarily consume 50 GiB of host storage immediately.
It grows as the guest writes data.

The base image and the writable disk are intentionally separate. Keeping the
base unchanged makes it possible to create another clean VM later.

## Cloud-init: the first-boot configurator

Cloud-init is software already installed in the Ubuntu cloud image. It turns a
generic image into our specific development VM when that VM first starts.

The script creates two configuration files:

```text
vm/cloud-init-<release>/meta-data
vm/cloud-init-<release>/user-data
```

`meta-data` gives the VM an identity, including its instance ID and hostname.
`user-data` is YAML beginning with `#cloud-config`; it declares the desired
first-boot setup.

Our user-data does the following:

- creates the configured developer account;
- permits that account to use `sudo` without a password;
- installs its SSH public key;
- disables SSH password authentication and direct root login;
- installs OpenSSH, certificates, and `curl`;
- adds Docker's APT repository;
- installs pinned Docker, Compose, Buildx, and containerd versions;
- enables Docker and adds the developer to the `docker` group.

QEMU exposes those two files as a small read-only virtual FAT disk labelled
`CIDATA`. Cloud-init recognizes that label as the **NoCloud datasource** and
reads the files from it.

```text
cloud-init directory on host → QEMU virtual seed disk (CIDATA) → cloud-init in guest
```

Cloud-init normally runs this setup once per instance ID. Editing `user-data`
after the VM exists does not reliably re-provision the existing machine. For a
clean rebuild, stop the VM first, then use a new `VM_DIR` or deliberately
replace the matching writable disk *and* cloud-init seed directory.

## SSH authentication and networking

The script copies a **public** key into the guest, never the private key. Your
private key remains on your host computer. This is why password login is
disabled and why SSH can authenticate safely.

QEMU uses user-mode networking (NAT) with this mapping:

```text
127.0.0.1:2222 on host → port 22 (SSH) in guest
```

Connect with:

```bash
ssh -p 2222 <guest-user>@127.0.0.1
```

The exact user is `VM_USERNAME` or the host username by default. The exact
host port is `SSH_PORT` or `2222` by default.

For development browser access, the Makefile reads the non-secret port
variables from the repository `.env` and passes them to `create-vm.sh`. The
script forwards the matching ports into the VM. Compose then forwards each VM
port to its container. Only the gateway publishes application ports
(ADR-0006), so `GATEWAY_HTTPS_PORT=8443` provides this complete route:

```text
host localhost:8443 → QEMU → VM:8443 → gateway container:8443 → service:8000
```

The launcher forwards PostgreSQL ports in `dev` and `local-backend` modes, and
Adminer's in `dev` mode. Production mode only forwards the gateway's ports.
Inside the VM, Compose publishes the database and Adminer ports on every guest
address (`VM_GUEST_BIND_ADDRESS=0.0.0.0`, set by the VM targets): QEMU forwards to
the guest's network address, not its loopback. QEMU itself only listens on the
host's `127.0.0.1`.

### Make-based VM workflow

The root Makefile is the host-side entry point. It starts QEMU, synchronizes
this repository into the guest with rsync, then runs Docker-oriented Make
targets through SSH inside the VM:

```text
make dev-docker-vm
  → start/wait for VM
  → rsync host repository to the guest
  → SSH into the guest
  → make dev-docker (Docker and Compose run inside the VM)
```

Useful targets are `make create-vm` (interactive full rebuild), `make
launch-vm`, `make stop-vm`, `make debug-create-vm`, and `make dev-docker-vm`. A fresh
VM receives `make` from cloud-init. `create-vm` deletes the visible `vm/`
directory only after an interactive confirmation, then provisions, syncs, and
cleanly shuts down the guest so it is ready for a normal later launch.

`make run-vm SERVICE=identity` keeps the backend process on the **physical
host** while Docker starts PostgreSQL and pgvector **inside the VM**. It
restarts the VM in `local-backend` mode, which deliberately does not forward
frontend or API ports; those ports must remain free for local Vite/Uvicorn
processes. It adds explicit database-only localhost forwards:

```text
local backend → host localhost:5432/5433 → QEMU → VM Docker database container
```

The local backend keeps using the existing `POSTGRES_HOST=localhost` setting.
This is useful when iterating on one backend without containerizing it; its
Uvicorn process and FastAPI `/docs` page remain local to the physical host.

### Development and production network modes

`create-vm.sh` selects its QEMU forwarding boundary with `VM_NETWORK_MODE`:

```bash
make launch-vm VM_NETWORK_MODE=dev   # default
make launch-vm VM_NETWORK_MODE=prod
```

Development mode forwards the gateway (`GATEWAY_PORT`, `GATEWAY_HTTPS_PORT`),
Grafana, Adminer and the databases using the ports passed by Make. FastAPI's `/docs`
pages are not routed by the gateway; open them by running the service on the
host (`make run SERVICE=<name>`). `local-backend` mode leaves app ports free
for host processes and is used with explicit database forwarding by
`make run-vm`. Production mode forwards the gateway's two ports and Grafana
on host loopback; the gateway remains the one public application edge.
Stop a running VM before changing modes because QEMU fixes its forwarded ports
at startup.

The production edge is the Traefik gateway (`srcs/gateway/`): it serves the
frontend's Nginx container and routes `/api/<service>/...` to the services
over the `edge` network. To run production Compose configuration, omit the
automatic development override:

```bash
docker compose -f compose.yaml --profile frontend --profile backend --profile databases up --build
```

Binding the forwarding rule to `127.0.0.1` means other computers on the LAN
cannot directly SSH into the VM. This is a good secure default. The guest can
still normally make outbound network connections for package downloads.

After cloud-init adds a user to the `docker` group, log out and back in before
expecting `docker ps` to work without `sudo`.

## QEMU virtual hardware

The script's most important QEMU concepts are:

| Concept | Meaning in our VM |
| --- | --- |
| `-m 6G` | guest RAM allocation (configurable with `VM_MEMORY`) |
| `-smp 4` | virtual CPU count (configurable with `VM_CPUS`) |
| `virtio` | efficient virtualization-aware disk/network device interface |
| `-accel kvm` / `hvf` | hardware virtualization acceleration |
| UEFI / OVMF / AAVMF | modern boot firmware for the AMD64/ARM64 guest |
| `-daemonize` | run QEMU in the background in normal mode |

UEFI needs two firmware files: read-only firmware code and a writable variables
file. The writable variables file is per VM because it stores persistent UEFI
state such as boot settings.

## Everyday operational commands

Start the VM:

```bash
make launch-vm
```

Start it with an interactive display and serial console for troubleshooting:

```bash
make debug-create-vm
```

Connect over SSH:

```bash
ssh -p 2222 <guest-user>@127.0.0.1
```

Once connected, check whether first-boot configuration finished:

```bash
cloud-init status --long
sudo journalctl -u cloud-final.service
sudo cat /var/log/cloud-init-output.log
```

Check Docker after reconnecting:

```bash
docker ps
docker compose version
```

## Common mistakes and how to reason about them

**“I changed an environment variable, but the VM did not change.”**  The
existing QCOW2 disk and cloud-init identity are preserved. The script starts
the existing VM rather than rebuilding it.

**“SSH is refused.”**  First check whether QEMU is running, then whether the
host port is already used, and finally inspect cloud-init logs using debug mode
or the guest console.

**“Docker says permission denied.”**  Reconnect after the user was added to the
`docker` group. Also remember that membership in this group is effectively
root-level access on the VM; only trusted accounts should receive it.

**“The VM cannot use all the newly configured disk space.”**  QEMU expanded the
virtual disk. Verify in the guest with `lsblk` and `df -h`; first-boot cloud-init
usually grows the partition/filesystem, but this behavior should be checked
instead of assumed.

**“I cannot start another VM.”**  It may be using the same `SSH_PORT` (default
2222). Give the second VM a distinct directory and port, for example:

```bash
make launch-vm VM_DIR="$PWD/vm-teammate" VM_SSH_PORT=2223
```

**“WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!” after I rebuilt the VM.**
SSH saves the VM server's public host key for `127.0.0.1:2222` in the host
computer's `~/.ssh/known_hosts`. A rebuilt VM has a new server key, so SSH
correctly refuses to silently trust it. If you intentionally rebuilt this
local VM, remove only the obsolete entry:

```bash
ssh-keygen -R '[127.0.0.1]:2222'
```

Then reconnect and accept the displayed new fingerprint:

```bash
ssh -p 2222 <guest-user>@127.0.0.1
```

If you connected with `localhost` rather than `127.0.0.1`, use
`ssh-keygen -R '[localhost]:2222'` instead. Do not remove a changed host key
when you did not intentionally rebuild the VM: in that case, investigate the
warning because it can indicate a real server-identity problem.

## What to remember versus what to look up

Memorize the system model, not long command lines:

- QEMU supplies virtual hardware; KVM/HVF makes it fast.
- The QCOW2 disk is persistent VM state.
- Cloud-init configures a generic cloud image at first boot.
- An SSH public key is installed in the VM; its private key stays on the host.
- Host port forwarding is how `localhost:2222` reaches guest SSH port 22.
- Cloud-init logs are the first place to investigate provisioning failures.

Exact QEMU arguments are appropriate to look up in this script or QEMU
documentation. In platform engineering, reproducible scripts and clear
runbooks are more valuable than memorizing obscure flags.

## FAQ

### What is the difference between QEMU/KVM and Vagrant?

They solve different layers of the problem and can be used together.

- **QEMU** is the VM emulator/virtualizer. It provides the virtual CPU,
  disks, network cards, firmware, and other virtual hardware.
- **KVM** is the Linux kernel's hardware-virtualization interface. QEMU uses
  it to run a compatible guest CPU efficiently. On Apple Silicon macOS, this
  role is performed by HVF instead.
- **Vagrant** is a developer workflow tool. It describes how to create,
  configure, start, stop, and share a repeatable development environment.
  Vagrant delegates the actual VM execution to a *provider*, commonly
  VirtualBox, VMware, Hyper-V, libvirt, or sometimes QEMU.

In this project, `shared/script/create-vm.sh` is a small, explicit alternative to the part
of Vagrant that provisions and starts a VM. It calls QEMU directly, so the
virtual hardware, cloud-init configuration, disk locations, and network
forwarding are visible in the entry point and its focused modules.

Use a direct QEMU script when we want few dependencies and precise control.
Use Vagrant when a team benefits from its standard lifecycle commands,
box ecosystem, and provider abstraction. Neither is automatically “more
professional”; the right choice depends on whether the added Vagrant layer
makes the team workflow simpler.

### What is the difference between a cloud image and an ISO?

An **ISO** is usually installation media: it behaves like a DVD containing an
operating-system installer. Booting it commonly opens an interactive process:
choose language, partition disks, create a user, configure networking, then
install the OS onto an empty virtual disk.

A **cloud image** is an already installed, minimal operating system disk. It
is intended to boot directly and receive its per-machine settings
automatically from cloud-init.

```text
ISO workflow:         boot installer → answer installation questions → reboot into installed OS
Cloud-image workflow: boot ready OS → cloud-init applies configuration → ready for SSH
```

For automated developer environments, the cloud-image workflow is usually a
better fit: it is faster, non-interactive, and reproducible. An ISO is useful
when learning manual OS installation, testing partitioning/storage layouts, or
installing an operating system that does not provide a suitable cloud image.

### Does QEMU require KVM?

No. QEMU can emulate a CPU entirely in software, but that is much slower.
KVM is the usual way for QEMU on Linux to use hardware virtualization. The
guest architecture must be compatible with the host CPU for this fast path.

### Is cloud-init only for public-cloud providers?

No. Public clouds popularized cloud-init, but it also works locally. The
script uses the NoCloud datasource: QEMU attaches local `user-data` and
`meta-data` files as a `CIDATA` seed disk. This gives a local VM much of the
same first-boot automation used by cloud providers.

### Why not put the SSH private key into the VM?

A private key proves your identity. Copying it into a VM increases the number
of places it can be stolen from and makes key rotation harder. The VM only
needs the public half of the key so that it can verify a login attempt made
from the host.

### How does SSH work concretely between my host and this VM?

There are two separate uses of cryptographic keys. They answer two different
security questions:

```text
1. “Is this really the VM I meant to contact?”
   VM host private key ── proves identity ──> saved VM host public key on host

2. “Is this really an allowed developer?”
   Host user private key ── proves identity ──> user public key in VM's authorized_keys
```

The connection itself proceeds like this:

1. Your SSH client connects to `127.0.0.1:2222`.
2. QEMU's port-forwarding rule sends that connection to port 22 in the VM.
3. The VM's SSH server (`sshd`) presents its **host key**. Your SSH client
   checks it against the key previously saved in `~/.ssh/known_hosts`.
4. Your SSH client proves that it owns the private key matching the public key
   installed by cloud-init in the VM's `~/.ssh/authorized_keys`.
5. SSH creates an encrypted connection, and `sshd` starts a shell as your
   guest user.

The host key identifies the **server/VM**. Your own key identifies the
**client/developer**. Do not confuse them: they are intentionally different
key pairs with opposite jobs.

### Why is it called cloud-init when we use it locally?

Cloud-init began as a way for cloud providers to customize a fresh generic VM
when they boot it for a customer. A provider can supply a hostname, users, SSH
keys, network settings, packages, and startup commands without making a
different Ubuntu image for every VM.

The same problem exists locally: we begin with one generic cloud image and
need a reproducible development VM. QEMU therefore gives cloud-init local
configuration files through the NoCloud datasource. “Cloud” describes the
original deployment model and image format; it does not mean this VM contacts
or requires a public cloud.

### Why do I receive a “possible man-in-the-middle attack” warning after rebuilding the VM?

SSH remembers the VM's host public key in `~/.ssh/known_hosts`. A newly built
VM generates a different host key, but it is still reached using the same
address, `127.0.0.1:2222`. SSH correctly treats an unexpected identity change
as suspicious: on a real network, it could mean someone is impersonating the
server.

For a VM you knowingly deleted and rebuilt, remove the old saved host key from
the **host computer**:

```bash
ssh-keygen -R '[127.0.0.1]:2222'
```

Then reconnect:

```bash
ssh -p 2222 <guest-user>@127.0.0.1
```

SSH will display the new host-key fingerprint and ask whether to trust it.
Because this VM is local and you intentionally rebuilt it, accepting the new
key is appropriate. If you did **not** rebuild the VM, stop and investigate
instead of removing the old key: the warning is doing its job.

Depending on the address used previously, there may also be an old `localhost`
entry to remove:

```bash
ssh-keygen -R '[localhost]:2222'
```
