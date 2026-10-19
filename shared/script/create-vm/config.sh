# Host platform, VM defaults, prerequisites, and guest identity.
init_config() {
    host_os=$(uname -s)
    case "$host_os" in
        Linux)
            acceleration=kvm
            ;;
        Darwin)
            acceleration=hvf
            ;;
        *) fail "unsupported host operating system: $host_os (supported: Linux, macOS)." ;;
    esac

    host_arch=$(uname -m)
    case "$host_arch" in
        x86_64)
            image_arch=amd64
            qemu_bin=qemu-system-x86_64
            ;;
        aarch64|arm64)
            image_arch=arm64
            qemu_bin=qemu-system-aarch64
            ;;
        *) fail "unsupported host architecture: $host_arch (supported: x86_64, aarch64)." ;;
    esac

    # An ARM64 Ubuntu guest on Apple silicon can use HVF for native CPU execution.
    # Running the amd64 image there would require slow, fully emulated CPU execution.
    if [[ "$host_os" == Darwin && "$image_arch" != arm64 ]]; then
        fail "macOS support is for Apple-silicon hosts (arm64) and starts a native ARM64 Ubuntu guest."
    fi

    for command_name in "$qemu_bin" qemu-img python3; do
        command -v "$command_name" >/dev/null 2>&1 || fail \
            "required command '$command_name' was not found."
    done
    if [[ "$acceleration" == kvm ]]; then
        [[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] || fail \
            "KVM is not accessible to this user at /dev/kvm. Ask your administrator to enable user access; this script will not use sudo."
    fi

    # Homebrew installs the EDK II firmware that QEMU needs to boot an ARM64 cloud
    # image under its QEMU share directory. Keep the standard locations too, so a
    # manually installed QEMU can still be used by setting ARM_UEFI_{CODE,VARS}.
    macos_qemu_share_dirs=()
    if [[ "$host_os" == Darwin ]]; then
        if command -v brew >/dev/null 2>&1; then
            qemu_brew_prefix=$(brew --prefix qemu 2>/dev/null || true)
            [[ -z "$qemu_brew_prefix" ]] || macos_qemu_share_dirs+=("$qemu_brew_prefix/share/qemu")
        fi
        macos_qemu_share_dirs+=(/opt/homebrew/share/qemu /usr/local/share/qemu)
    fi

    login_name=${USER:-$(id -un)}
    if [[ "$host_os" == Darwin ]]; then
        default_vm_dir=vm
    else
        default_vm_dir=/goinfre/$login_name/vm
    fi
    vm_dir=${VM_DIR:-$default_vm_dir}
    vm_username=${VM_USERNAME:-$login_name}
    vm_hostname=${VM_HOSTNAME:-dev-$vm_username}
    ssh_public_key=${SSH_PUBLIC_KEY:-$HOME/.ssh/id_rsa.pub}
    disk_size_gb=${DISK_SIZE_GB:-50}
    vm_memory=${VM_MEMORY:-6G}
    vm_cpus=${VM_CPUS:-4}
    ssh_port=${SSH_PORT:-2222}
    vm_network_mode=${VM_NETWORK_MODE:-dev}
    vm_debug=${VM_DEBUG:-0}
    # Pin Docker's packages so every VM rebuild receives the same toolchain.
    docker_engine_version=${DOCKER_ENGINE_VERSION:-5:29.9.0-1~ubuntu.24.04~noble}
    docker_compose_version=${DOCKER_COMPOSE_VERSION:-5.6.0-1~ubuntu.24.04~noble}
    docker_buildx_version=${DOCKER_BUILDX_VERSION:-0.38.0-1~ubuntu.24.04~noble}
    containerd_version=${CONTAINERD_VERSION:-2.4.1-2~ubuntu.24.04~noble}
    # Pin one published image build so teammates start from matching guest images.
    ubuntu_image_release=20260926
    disk_path=$vm_dir/ubuntu-server-cloud-$image_arch-$ubuntu_image_release.qcow2
    image_dir=$vm_dir/images
    base_image=$image_dir/ubuntu-24.04-server-cloudimg-$image_arch-$ubuntu_image_release.img
    seed_dir=$vm_dir/cloud-init-$ubuntu_image_release
    [[ "$vm_username" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]] || fail \
        "VM_USERNAME must be a valid simple Linux username."
    [[ "$vm_hostname" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || fail \
        "VM_HOSTNAME must contain only letters, digits, dots, and hyphens."
    [[ -r "$ssh_public_key" ]] || fail \
        "SSH public key not found at '$ssh_public_key'. Create one with ssh-keygen or set SSH_PUBLIC_KEY."
    [[ "$disk_size_gb" =~ ^[1-9][0-9]*$ ]] || fail \
        "DISK_SIZE_GB must be a positive whole number of GiB (for example, 50)."
    [[ "$vm_cpus" =~ ^[1-9][0-9]*$ ]] || fail \
        "VM_CPUS must be a positive whole number (for example, 4)."
    [[ "$ssh_port" =~ ^[0-9]+$ ]] && (( ssh_port >= 1 && ssh_port <= 65535 )) || fail \
        "SSH_PORT must be a TCP port between 1 and 65535."
    [[ "$vm_memory" =~ ^[1-9][0-9]*[GgMm]$ ]] || fail \
        "VM_MEMORY must be a positive number followed by G or M (for example, 6G)."
    [[ "$vm_debug" == 0 || "$vm_debug" == 1 ]] || fail \
        "VM_DEBUG must be 0 or 1."
    for package_version in "$docker_engine_version" "$docker_compose_version" "$docker_buildx_version" "$containerd_version"; do
        [[ "$package_version" =~ ^[A-Za-z0-9:.+~=-]+$ ]] || fail \
            "Docker package versions may contain only letters, digits, colon, dot, plus, tilde, equals, and hyphen."
    done

    read -r key_type key_data _ < "$ssh_public_key"
    [[ "$key_type" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))$ && -n "$key_data" ]] || fail \
        "'$ssh_public_key' does not look like a supported OpenSSH public key."
    ssh_key=$(<"$ssh_public_key")
}
