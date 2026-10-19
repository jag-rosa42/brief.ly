# Verify or create the Ubuntu image and writable VM disk.
prepare_image() {
    mkdir -p "$vm_dir" "$image_dir"
    chmod 700 "$vm_dir"

    needs_first_boot=false
    if [[ ! -e "$disk_path" ]]; then
        needs_first_boot=true
        # Ubuntu publishes cloud-init-enabled KVM images separately per CPU architecture.
        image_name="ubuntu-24.04-server-cloudimg-$image_arch.img"
        release_url="https://cloud-images.ubuntu.com/releases/noble/release-$ubuntu_image_release"
        image_url="$release_url/ubuntu-24.04-server-cloudimg-$image_arch.img"
        checksum_url="$release_url/SHA256SUMS"

        python3 "$module_dir/download_image.py" "$base_image" "$image_url" "$checksum_url" "$image_name"
        printf 'Creating independent writable VM disk: %s\n' "$disk_path"
        qemu-img convert -f qcow2 -O qcow2 "$base_image" "$disk_path"
        qemu-img resize "$disk_path" "${disk_size_gb}G"
    else
        [[ -f "$disk_path" ]] || fail "VM disk path exists but is not a regular file: $disk_path"
        image_info=$(qemu-img info "$disk_path") || fail "could not read VM disk: $disk_path"
        [[ "$image_info" == *"file format: qcow2"* ]] || fail \
            "existing VM disk is not qcow2; refusing to use it: $disk_path"
    fi
}
