#!/usr/bin/env bash

# Create a per-developer Ubuntu cloud VM and start it with QEMU acceleration.
set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  make launch-vm
  VM_NETWORK_MODE=prod GATEWAY_PORT=8080 ./shared/script/create-vm.sh

On Linux, the default VM directory is /goinfre/$USER/vm and QEMU uses KVM.
On macOS, the default is ./vm and QEMU uses Hypervisor.framework (HVF).
Install QEMU first (for example, `brew install qemu` on macOS). The script
downloads the pinned Ubuntu 24.04 LTS cloud image matching the host
architecture, makes a private writable copy, and configures its first boot
with your SSH public key.

Environment settings (make launch-vm supplies the port values from .env):
  VM_DIR             VM working directory (default: /goinfre/$USER/vm on Linux; ./vm on macOS)
  VM_USERNAME        Guest account (default: current host username)
  VM_HOSTNAME        Guest hostname (default: dev-<VM_USERNAME>)
  SSH_PUBLIC_KEY     Public key file (default: ~/.ssh/id_rsa.pub)
  DISK_SIZE_GB       Virtual disk maximum in GiB (default: 50)
  VM_MEMORY          Guest RAM (default: 6G)
  VM_CPUS            Guest vCPUs (default: 4)
  SSH_PORT           Host port forwarded to guest port 22 (default: 2222)
  VM_NETWORK_MODE    dev forwards app and database ports; local-backend forwards database ports but reserves app ports for host processes; prod forwards only GATEWAY_PORT (default: dev)
  VM_DEBUG           Show guest VGA window and serial console in foreground (default: 0; set to 1 to debug)
  DOCKER_ENGINE_VERSION   Docker Engine/CLI apt version (default: 5:29.9.0-1~ubuntu.24.04~noble)
  DOCKER_COMPOSE_VERSION  Docker Compose plugin apt version (default: 5.6.0-1~ubuntu.24.04~noble)
  DOCKER_BUILDX_VERSION   Docker Buildx plugin apt version (default: 0.38.0-1~ubuntu.24.04~noble)
  CONTAINERD_VERSION      containerd.io apt version (default: 2.4.1-2~ubuntu.24.04~noble)
  AMD64_UEFI_CODE    AMD64 OVMF code firmware file, if not auto-detected
  AMD64_UEFI_VARS    AMD64 OVMF writable variables template, if not auto-detected
  ARM_UEFI_CODE      ARM64 UEFI code firmware file, if not auto-detected
  ARM_UEFI_VARS      ARM64 UEFI writable variables template, if not auto-detected
  Port variables     Direct calls must supply GATEWAY_PORT for prod; app and database ports for dev; database ports for local-backend.
USAGE
}

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi
(( $# == 0 )) || { usage >&2; exit 2; }

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
module_dir=$script_dir/create-vm
for module in config network image seed qemu; do
    source "$module_dir/$module.sh"
done

main() {
    # config.sh: detect the host, set VM options, and validate the SSH key.
    init_config
    # network.sh: validate supplied ports and build QEMU forwarding rules.
    configure_network
    # image.sh: verify or create the VM disk; download_image.py verifies Ubuntu.
    prepare_image
    # seed.sh: create or check first-boot files; write_seed.py writes their contents.
    ensure_seed
    # qemu.sh: assemble the virtual hardware and firmware arguments.
    build_qemu_args
    # qemu.sh: print the VM configuration before startup.
    print_vm_summary
    # qemu.sh: launch QEMU with the assembled arguments.
    start_qemu
}

main
