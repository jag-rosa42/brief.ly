# Build the virtual hardware, report the chosen settings, and start QEMU.
build_qemu_args() {
    qemu_args=(
        -m "$vm_memory"
        -smp "$vm_cpus"
        -drive "file=$disk_path,format=qcow2,if=virtio"
        -blockdev "driver=vvfat,node-name=cloudseed,read-only=on,dir=$seed_dir,label=CIDATA"
        -device virtio-blk-pci,drive=cloudseed
        -netdev "$netdev_config"
        -device virtio-net-pci,netdev=net0
    )

    if [[ "$image_arch" == amd64 ]]; then
        qemu_args+=( -accel "$acceleration" -cpu host -boot order=c )
        firmware_code=${AMD64_UEFI_CODE:-}
        firmware_vars_template=${AMD64_UEFI_VARS:-}
        for firmware_pair in \
            /usr/share/edk2/ovmf/OVMF_CODE.fd\|/usr/share/edk2/ovmf/OVMF_VARS.fd \
            /usr/share/OVMF/OVMF_CODE_4M.fd\|/usr/share/OVMF/OVMF_VARS_4M.fd \
            /usr/share/OVMF/OVMF_CODE.fd\|/usr/share/OVMF/OVMF_VARS.fd; do
            candidate_code=${firmware_pair%%|*}
            candidate_vars=${firmware_pair#*|}
            [[ -n "$firmware_code" || ! -r "$candidate_code" ]] || firmware_code=$candidate_code
            [[ -n "$firmware_vars_template" || ! -r "$candidate_vars" ]] || firmware_vars_template=$candidate_vars
        done
        [[ -r "$firmware_code" ]] || fail \
            "AMD64 OVMF UEFI code firmware was not found; install the host OVMF package or set AMD64_UEFI_CODE."
        [[ -r "$firmware_vars_template" ]] || fail \
            "AMD64 OVMF UEFI variables template was not found; install the host OVMF package or set AMD64_UEFI_VARS."
        if [[ ! -e "$firmware_vars" ]]; then
            cp "$firmware_vars_template" "$firmware_vars"
            chmod 600 "$firmware_vars"
        fi
        qemu_args+=(
            -drive "if=pflash,format=raw,unit=0,readonly=on,file=$firmware_code"
            -drive "if=pflash,format=raw,unit=1,file=$firmware_vars"
        )
    else
        qemu_args+=( -machine "virt,accel=$acceleration" -cpu host -boot order=c )
        firmware_code=${ARM_UEFI_CODE:-}
        firmware_vars_template=${ARM_UEFI_VARS:-}
        for candidate in /usr/share/AAVMF/AAVMF_CODE.fd /usr/share/edk2/aarch64/QEMU_EFI-pflash.raw; do
            [[ -n "$firmware_code" || ! -f "$candidate" ]] || firmware_code=$candidate
        done
        for candidate in /usr/share/AAVMF/AAVMF_VARS.fd /usr/share/edk2/aarch64/vars-template-pflash.raw; do
            [[ -n "$firmware_vars_template" || ! -f "$candidate" ]] || firmware_vars_template=$candidate
        done
        for qemu_share_dir in "${macos_qemu_share_dirs[@]}"; do
            candidate=$qemu_share_dir/edk2-aarch64-code.fd
            [[ -n "$firmware_code" || ! -r "$candidate" ]] || firmware_code=$candidate
            candidate=$qemu_share_dir/edk2-arm-vars.fd
            [[ -n "$firmware_vars_template" || ! -r "$candidate" ]] || firmware_vars_template=$candidate
        done
        [[ -r "$firmware_code" ]] || fail \
            "ARM64 UEFI code firmware was not found; install QEMU with Homebrew or set ARM_UEFI_CODE."
        [[ -r "$firmware_vars_template" ]] || fail \
            "ARM64 UEFI variables template was not found; install QEMU with Homebrew or set ARM_UEFI_VARS."
        if [[ ! -e "$firmware_vars" ]]; then
            cp "$firmware_vars_template" "$firmware_vars"
            chmod 600 "$firmware_vars"
        fi
        qemu_args+=(
            -drive "if=pflash,format=raw,unit=0,readonly=on,file=$firmware_code"
            -drive "if=pflash,format=raw,unit=1,file=$firmware_vars"
        )
    fi
}

print_vm_summary() {
    printf '\nStarting Ubuntu 24.04 LTS %s VM\n' "$image_arch"
    printf '  Disk: %s\n' "$disk_path"
    printf '  User: %s (SSH key login; password login disabled)\n' "$vm_username"
    printf '  RAM: %s   CPUs: %s\n' "$vm_memory" "$vm_cpus"
    printf '  SSH: localhost:%s -> guest:22\n' "$ssh_port"
    case "$vm_network_mode" in
        dev)
            printf '  Network mode: dev (frontend, FastAPI services, and Adminer are forwarded from the supplied ports)\n'
            ;;
        local-backend)
            printf '  Network mode: local-backend (app ports are free for host processes)\n'
            ;;
        prod)
            printf '  Network mode: prod (only GATEWAY_PORT=%s is forwarded)\n' "$gateway_port"
            ;;
    esac
    if [[ "$vm_network_mode" == dev || "$vm_network_mode" == local-backend ]]; then
        printf '  Database forwarding: localhost:%s and localhost:%s -> VM Docker databases\n' "$postgres_port" "$ai_postgres_port"
    fi
    if [[ "$needs_first_boot" == true ]]; then
        printf '  First boot will create the guest user and unique SSH host keys using cloud-init.\n'
    fi
}

start_qemu() {
    # Cloud-init is non-interactive, so normal boots run headlessly in the
    # background. Debug mode keeps QEMU in the foreground, opens the guest VGA
    # display, and connects the serial console and monitor to this terminal.
    if [[ "$vm_debug" == 1 ]]; then
        printf 'Debug mode: QEMU stays in the foreground with a display window; use Ctrl-A C to switch between the serial console and QEMU monitor.\n'
        if [[ "$host_os" == Darwin ]]; then
            qemu_args+=( -display default -serial mon:stdio )
        else
            qemu_args+=( -display gtk -serial mon:stdio )
        fi
    else
        qemu_args+=( -display none -daemonize )
    fi

    exec "$qemu_bin" "${qemu_args[@]}"
}
