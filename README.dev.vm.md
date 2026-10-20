# VM development environment

Run the development Compose stack inside an Ubuntu virtual machine (VM). QEMU runs the guest, and Docker Compose runs the services inside it. This gives the stack a separate Linux runtime while forwarding browser-facing ports to your host. For locally running application processes with VM databases, see [README.dev.md](README.dev.md). For Compose on the host, see [README.docker.md](README.docker.md).

## Prerequisites and configuration

Complete these steps **on your host computer**, from the repository root. QEMU runs the VM, `rsync` copies the project into it, and SSH opens a secure connection to it. The same setup is required for `make vm-databases` in [local development](README.dev.md).

### 1. Check required tools

Copy and paste this block into your terminal. It reports `OK` or `MISSING` for each tool and checks Linux KVM access. It does not install or change anything.

```bash
bash <<'CHECK'
case "$(uname -s)/$(uname -m)" in
    Linux/x86_64) qemu=qemu-system-x86_64 ;;
    Linux/aarch64|Darwin/arm64) qemu=qemu-system-aarch64 ;;
    *) echo "Unsupported host: use Linux (x86_64/ARM64) or an Apple Silicon Mac."; exit 1 ;;
esac
for tool in "$qemu" qemu-img rsync ssh ssh-keygen ssh-add python3 lsof; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "OK       $tool"
    else
        echo "MISSING  $tool"
    fi
done
if [ "$(uname -s)" = Linux ]; then
    if [ -c /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
        echo "OK       KVM access"
    else
        echo "MISSING  KVM access — ask your administrator to enable /dev/kvm access."
    fi
fi
CHECK
```

If tools are missing, use the commands for your system, then rerun the check.

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install rsync openssh-client python3 lsof qemu-utils
case "$(uname -m)" in
    x86_64) sudo apt install qemu-system-x86 ovmf ;;
    aarch64) sudo apt install qemu-system-arm qemu-efi-aarch64 ;;
esac
```

For other Linux distributions, use the equivalent packages from your package manager.

**macOS — Apple Silicon**, with [Homebrew](https://brew.sh/) installed:

```bash
brew install qemu rsync openssh python
```

### 2. Check or create your SSH key pair

An SSH key pair contains a **public key** (`.pub`), which is copied into the VM, and a **private key**, which stays on your host. The repository defaults to `~/.ssh/id_rsa.pub`.

Check the default public key and its fingerprint (a short identifier for the key):

```bash
ls -l ~/.ssh/id_rsa.pub
ssh-keygen -lf ~/.ssh/id_rsa.pub
```

If both commands succeed, reuse that key. If you already use another key, such as `~/.ssh/id_ed25519.pub`, check that path instead and use it in step 3.

If the public key is missing, first check whether its private key already exists:

```bash
ls -l ~/.ssh/id_rsa
```

If the private key exists, recover its public key **only when the `.pub` file is missing**:

```bash
ssh-keygen -y -f ~/.ssh/id_rsa > ~/.ssh/id_rsa.pub
```

If neither file exists, create a new pair:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

Follow the prompts and choose a passphrase to protect the private key. **Do not overwrite an existing key.** Verify the new public key:

```bash
ssh-keygen -lf ~/.ssh/id_rsa.pub
```

The Makefile connects without interactive password prompts. Load your private key into the SSH agent, which keeps it available for those connections:

```bash
# Run this only if no SSH agent is available in your terminal:
eval "$(ssh-agent -s)"

ssh-add ~/.ssh/id_rsa
ssh-add -l
```

Use your actual private-key path if you chose a different key. Enter its passphrase when prompted by `ssh-add`; `ssh-add -l` should then list its fingerprint. You may need to load it again in a later session.

### 3. Create `.env` and set your public-key path

Create the root configuration only if it does not already exist:

```bash
make init-env
```

Open `.env` in your editor and set its existing `SSH_PUBLIC_KEY` line to the public key you verified:

```dotenv
SSH_PUBLIC_KEY=$(HOME)/.ssh/id_rsa.pub
```

For an Ed25519 key, use this instead:

```dotenv
SSH_PUBLIC_KEY=$(HOME)/.ssh/id_ed25519.pub
```

`$(HOME)` is expanded by the root Makefile to your home directory. You can also use the full absolute path to your `.pub` file. Set the **path**, not the key's contents, and do not point to the private key. For a nonstandard private-key filename, load it with `ssh-add` as shown above so SSH can find it.

### 4. Choose where to store the VM

Set `VM_DIR` in the root `.env` to a directory on a disk with enough free space. This stores the VM disk, downloaded Ubuntu image, and first-boot files. Docker images, containers, and database data live inside the VM disk.

The default stores everything in the project's `vm/` directory:

```dotenv
VM_DIR=$(CURDIR)/vm
```

If your project is on a storage-limited home directory, choose another location. For example, on a 42 Linux workstation with `/goinfre` available, replace the line with:

```dotenv
VM_DIR=/goinfre/your-login/transcendence-vm
```

Replace `your-login` with your actual login. Use a directory you can write to; recreation replaces only the current guest’s disk, first-boot files, and firmware state. Check your campus's cleanup policy before using `/goinfre` for data you need to keep.

The default virtual disk capacity is **50 GiB**. Its host file grows as data is written, so it does not reserve all 50 GiB immediately. As a practical budget, allow **at least 60 GiB of free host space** for the disk to grow, plus the downloaded image and overhead. Large Docker builds or datasets can require more space or a larger virtual disk.

Check available space on the disk where you will store the VM:

```bash
# Default location (run from the repository root):
df -h .

# For the example above, check its existing parent directory instead:
df -h /goinfre
```

Read the `Avail` column. Set `VM_DIR` before the first launch: changing it later does not move an existing VM or its data.

### 5. Set CPU, RAM, and disk capacity

The VM script uses these defaults:

| Resource | Default | Setting |
| --- | --- | --- |
| CPU | 4 virtual CPUs | `VM_CPUS=4` |
| RAM | 6 GiB | `VM_MEMORY=6G` |
| Disk | 50 GiB maximum virtual capacity | `DISK_SIZE_GB=50` |
| GPU | No host GPU access configured | No GPU setting is available |

Virtual CPUs share your host's processor; they do not reserve four physical cores exclusively. The RAM setting is memory available to the guest, with additional host memory needed for QEMU itself. The disk grows as used, as explained in step 4. The VM normally runs without a display, and this setup does not expose the Mac's GPU for AI workloads.

To change the allocation, add these lines to the root `.env` and adjust the values:

```dotenv
export VM_CPUS=4
export VM_MEMORY=6G
export DISK_SIZE_GB=50
```

Keep `export` on these lines so the VM process receives the settings. CPU must be a positive whole number; RAM accepts `G` or `M` (for example, `4G` or `4096M`); disk size is a positive whole number in GiB.

CPU and RAM changes take effect when QEMU restarts:

```bash
make stop-vm
make launch-vm
```

Changing `DISK_SIZE_GB` only affects a **new disk**; it does not resize an existing VM. Do not recreate an existing VM just to apply CPU or RAM changes.

**Example: MacBook with the original M1 chip**

The original M1 has an 8-core CPU ([Apple specifications](https://www.apple.com/ca/mac/compare/?modelList=MacBook-Air-M1%2CMacBookPro-13-M1)). Start with the following allocation based on your Mac's total memory:

| Mac memory | VM CPUs | VM RAM | VM disk |
| --- | --- | --- | --- |
| 8 GB | 4 | `3G` | 50 GiB |
| 16 GB | 4 | `6G` | 50 GiB |

These are starting recommendations, not measured requirements for the full stack. On an 8 GB Mac, `3G` leaves more room for macOS, your editor, and browser; run only the services you need if builds or containers run out of memory. On a 16 GB Mac, the defaults are a reasonable starting point. Watch macOS Activity Monitor's **Memory Pressure** while developing; reduce VM RAM or concurrent workloads if pressure stays high.

For an **8 GB M1 MacBook**, use:

```dotenv
export VM_CPUS=4
export VM_MEMORY=3G
export DISK_SIZE_GB=50
```

### 6. Create the VM with `make create-vm`

After configuring `.env`, run this from the repository root:

```bash
make create-vm
```

The command asks for confirmation. Enter `y` to continue, or press Enter to cancel. It stops the existing VM, removes the current guest’s state, and creates a fresh guest using your configured CPU, RAM, and disk capacity.

**Recreation is destructive:** it deletes the current architecture and Ubuntu image build’s `.qcow2` disk, matching `cloud-init-<build>/` directory, and UEFI variables file. All Docker images and database data inside that disk are lost. Back up any data you need before confirming; there is no automatic rollback. The `images/` download cache, unrelated files, and other builds’ disks are preserved.

When no VM disk exists, the launch process downloads Ubuntu, creates the disk, sets up your SSH account, and installs Docker and Compose inside the guest. Keep internet access available and wait for first-boot setup and project synchronization to finish. The VM is then running, but the application containers have not been started.

Check that you can connect and that Docker is ready:

```bash
make connect-vm
# Inside the VM:
docker --version
docker compose version
exit
```

For later starts, use `make launch-vm`. To apply CPU or RAM changes, use `make stop-vm` followed by `make launch-vm`; recreation is unnecessary. When ready to start the application, continue with the VM commands below.

### 7. Start the application inside the VM

Run these commands **on your host**, from the repository root, after preparing the service `.env` files from their `.env.example` templates.

**Start the full development stack:**

```bash
make vm
```

This stops and restarts the VM with development port forwarding, synchronizes your project, configuration, and secrets, then builds and starts the application containers inside the VM. Containers run in the background, so the command returns when startup completes. The existing VM disk and database data are preserved.

**Start a specific service and its dependencies:**

```bash
make vm SERVICE=identity
```

Replace `identity` with a service name from `compose.yaml`, such as `personalization`, `content-management`, `ai-processing`, `morning-briefing`, or `frontend`. For identity, Compose also starts PostgreSQL and runs the required database setup before starting the API.

`SERVICE` selects what Compose builds and starts; it does not guarantee that all other services are stopped. Previously created containers with a restart policy can start again when the VM restarts. Both forms of `make vm` restart the whole VM, briefly interrupting any services already running there.

Start with `make vm SERVICE=identity` when working on that backend, especially on a memory-limited laptop. Use `make vm` when you need the complete application.

Check the result and inspect logs:

```bash
make ps-vm
make logs-vm SERVICE=identity
```

Press Ctrl+C to stop following logs; the containers keep running. With the default ports in `.env`, open `http://localhost:8081/docs` for identity, or `http://localhost:5173` for the frontend when it is running.

### 8. Stop the VM and keep a restore point

**For everyday use, just shut down the VM:**

```bash
make stop-vm
```

This asks Ubuntu to shut down cleanly and waits for QEMU to exit. Your installed software, Docker images, and database data remain on the VM disk. **No separate “save” command is needed.** Running programs stop; their RAM contents are not saved.

To continue later:

```bash
make launch-vm
```

This boots the same disk. Use `make vm` or `make vm SERVICE=identity` when you also want to build and start application containers. To stop only the containers while leaving Ubuntu running, use `make down-vm`.

**Optional: keep a restore point**

After `make stop-vm` finishes successfully, copy the **entire `vm/` directory** to another location, using your file manager if you prefer. If you changed `VM_DIR`, copy that directory instead. Keep the VM stopped until copying finishes, and keep the backup outside the original directory.

That copy is a restore point for your VM's files and databases. It is a stopped-VM backup, not a snapshot of RAM or running programs. Keep the copy untouched and continue working with the original VM.

**What is inside `vm/`?**

| File or directory | Purpose |
| --- | --- |
| `ubuntu-server-cloud-<architecture>-<build>.qcow2` | The working VM disk: Ubuntu, installed software, Docker images, and database data. |
| `cloud-init-<build>/` | First-boot configuration, including the guest account and SSH public key setup. |
| `<architecture>-uefi-vars-<build>.fd` | Saved firmware settings used when booting the VM. |
| `images/` | The downloaded Ubuntu base image used to create a fresh VM disk. It does not contain your working database data. |

Copying the whole directory keeps these files together. Allow enough free space for the copy, and keep it private and out of Git because the guest disk contains configuration, secrets, and database data.

**To restore:** stop the current VM, copy your backup into a new working directory, set `VM_DIR` in the root `.env` to that directory, and run `make launch-vm`. Keep the backup itself untouched so you can restore it again. Use the same host architecture and VM image-build configuration, because the scripts select the disk by those values. Do not use `make create-vm` to restore: it replaces the guest disk.

Keep your host project, `.env`, and SSH private key available too. Launching the VM synchronizes the current host project into the guest; restoring the VM does not roll back your host files.

### 9. Typical backend workflow

Run on the host, from the repository root:

```bash
make create-vm           # First time only; recreating deletes existing guest data
make vm SERVICE=identity # Start your backend and its dependencies
make ps-vm               # Check container status
# Edit source files on the host, then:
make vm-sync             # Copy changes; development source reloads automatically
```

Test at `http://localhost:8081/docs` for identity, or use your service's port from `.env`. Rebuild with `make vm SERVICE=identity` after dependency or image changes.

If a bug occurs, run `make logs-vm SERVICE=identity`, or `make connect-vm` to inspect Ubuntu directly. Keep editing source on the host.

When finished: **Ctrl+D** or `exit` leaves SSH without stopping the VM. To shut it down, run **`sudo poweroff` inside the VM**, or **`make stop-vm` from a host terminal**. Your disk and database data are preserved.

### 10. VM command reference

Run these commands on the host. Replace `<name>` with a Compose service such as `identity`.

| Command | What it does |
| --- | --- |
| `make create-vm` | Create a fresh guest; **deletes existing guest data after confirmation**. |
| `make launch-vm` | Start or reuse the VM and sync files; does not start the application stack. |
| `make vm` | Restart the VM, sync, build, and start the full development stack. |
| `make vm SERVICE=<name>` | Restart the VM, sync, build, and start one service with its dependencies. |
| `make vm-sync` | Copy host files, configuration, and secrets into the running VM. |
| `make ps-vm` | Show container status. |
| `make logs-vm` | Follow all development container logs. |
| `make logs-vm SERVICE=<name>` | Follow logs for one service. |
| `make connect-vm` | Start or reuse the VM, sync, and open an SSH shell. |
| `make down-vm` | Stop and remove development containers; keep database volumes and the VM running. |
| `make stop-vm` | Shut down the VM; keep its disk and data. |
| `make clean-vm` | Remove development containers and project images; keep database volumes. |
| `make re-vm` | Clean, rebuild, and start the development stack. |
| `make reset-db-vm` | Remove development containers and volumes; **deletes database data**. |
| `make fclean-vm` | Remove project images and volumes after confirmation; **deletes database data**. |
| `make debug-create-vm` | Run QEMU in the foreground to troubleshoot boot problems. |
| `make prod` | Restart in production network mode, build, and run production Compose. |

## Default Ubuntu and Docker versions

New guests use the defaults defined in [the VM configuration script](shared/script/create-vm/config.sh). Pinning the image build and package versions gives developers the same starting environment.

| Component | Default version | Override variable |
| --- | --- | --- |
| Ubuntu cloud image | 24.04 LTS (Noble), image build `20260926`; `amd64` or `arm64` to match the host | Fixed in the script |
| Docker Engine and CLI (`docker-ce`, `docker-ce-cli`) | `5:29.9.0-1~ubuntu.24.04~noble` | `DOCKER_ENGINE_VERSION` |
| Docker Compose plugin (`docker-compose-plugin`) | `5.6.0-1~ubuntu.24.04~noble` | `DOCKER_COMPOSE_VERSION` |
| Docker Buildx plugin (`docker-buildx-plugin`) | `0.38.0-1~ubuntu.24.04~noble` | `DOCKER_BUILDX_VERSION` |
| Container runtime (`containerd.io`) | `2.4.1-2~ubuntu.24.04~noble` | `CONTAINERD_VERSION` |

