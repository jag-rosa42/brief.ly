# Create first-boot cloud-init files, or verify the original seed.
ensure_seed() {
    if [[ "$needs_first_boot" == true ]]; then
        # No password is embedded in the image. Each first boot receives this
        # developer's account name and public key through a read-only NoCloud seed.
        mkdir -p "$seed_dir"
        chmod 700 "$seed_dir"
        instance_id="dev-${login_name}-$(date +%s)"
        python3 "$module_dir/write_seed.py" "$seed_dir" "$vm_username" "$vm_hostname" "$instance_id" "$ssh_key" \
            "$image_arch" "$docker_engine_version" "$docker_compose_version" "$docker_buildx_version" "$containerd_version"
        chmod 700 "$seed_dir"
    else
        [[ -f "$seed_dir/user-data" && -f "$seed_dir/meta-data" ]] || fail \
            "cloud-init seed is missing. Refusing to boot without the original per-VM identity files: $seed_dir"
    fi
}
