# Remove only the current guest's state; retain cached images and other files.
# The caller must stop the guest and obtain confirmation before calling this.
reset_vm_state() {
    command -v lsof >/dev/null 2>&1 || fail "lsof is required before resetting VM state."
    for target in "$disk_path" "$firmware_vars" "$seed_dir"; do
        [[ ! -L "$target" ]] || fail "refusing to reset symbolic link: $target"
    done
    for target in "$disk_path" "$firmware_vars"; do
        [[ ! -e "$target" || -f "$target" ]] || fail "expected a VM file: $target"
    done
    [[ ! -e "$seed_dir" || -d "$seed_dir" ]] || fail "expected a first-boot directory: $seed_dir"
    for target in "$disk_path" "$firmware_vars"; do
        if [[ -e "$target" ]] && lsof "$target" >/dev/null 2>&1; then
            fail "refusing to reset VM state still opened by another process: $target"
        fi
    done
    rm -f -- "$disk_path" "$firmware_vars"
    rm -rf -- "$seed_dir"
}
