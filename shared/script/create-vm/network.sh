# Validate the ports supplied by the caller and build QEMU's host forwards.
required_port() {
    local name=$1
    local value=${!name-}

    [[ "$value" =~ ^[1-9][0-9]*$ ]] || fail \
        "$name must be supplied as a numeric TCP port (make launch-vm reads it from .env)."
    (( ${#value} <= 5 )) && (( 10#$value <= 65535 )) || fail \
        "$name must be a TCP port between 1 and 65535."
}

configure_network() {
    # The Makefile includes .env and passes only the required, non-secret ports.
    # Direct callers must pass the same variables in their environment.
    case "$vm_network_mode" in
        dev|development)
            vm_network_mode=dev
            for port_name in FRONTEND_PORT ADMINER_PORT IDENTITY_PORT \
                PERSONALIZATION_PORT CONTENT_MANAGEMENT_PORT AI_PROCESSING_PORT \
                MORNING_BRIEFING_PORT; do
                required_port "$port_name"
            done
            forward_port_names=(
                SSH_PORT FRONTEND_PORT IDENTITY_PORT PERSONALIZATION_PORT
                CONTENT_MANAGEMENT_PORT AI_PROCESSING_PORT MORNING_BRIEFING_PORT ADMINER_PORT
            )
            forward_port_values=(
                "$ssh_port" "$FRONTEND_PORT" "$IDENTITY_PORT" "$PERSONALIZATION_PORT"
                "$CONTENT_MANAGEMENT_PORT" "$AI_PROCESSING_PORT" "$MORNING_BRIEFING_PORT" "$ADMINER_PORT"
            )
            ;;
        prod|production)
            vm_network_mode=prod
            required_port GATEWAY_PORT
            gateway_port=$GATEWAY_PORT
            forward_port_names=(SSH_PORT GATEWAY_PORT)
            forward_port_values=("$ssh_port" "$gateway_port")
            ;;
        local|local-backend)
            vm_network_mode=local-backend
            forward_port_names=(SSH_PORT)
            forward_port_values=("$ssh_port")
            ;;
        *) fail "VM_NETWORK_MODE must be dev, local-backend, or prod." ;;
    esac

    if [[ "$vm_network_mode" == dev || "$vm_network_mode" == local-backend ]]; then
        required_port POSTGRES_PORT
        required_port AI_POSTGRES_PORT
        postgres_port=$POSTGRES_PORT
        ai_postgres_port=$AI_POSTGRES_PORT
        forward_port_names+=(POSTGRES_PORT AI_POSTGRES_PORT)
        forward_port_values+=("$postgres_port" "$ai_postgres_port")
    fi

    # QEMU cannot bind the same host port twice.
    for forward_index in "${!forward_port_values[@]}"; do
        for previous_index in "${!forward_port_values[@]}"; do
            (( previous_index < forward_index )) || continue
            [[ "${forward_port_values[$forward_index]}" != "${forward_port_values[$previous_index]}" ]] || fail \
                "${forward_port_names[$forward_index]} and ${forward_port_names[$previous_index]} both use port ${forward_port_values[$forward_index]}."
        done
    done

    # Compose publishes container ports inside the guest; QEMU forwards them
    # from localhost on the host. SSH always maps to guest port 22.
    netdev_config="user,id=net0,hostfwd=tcp:127.0.0.1:${ssh_port}-:22"
    for forward_index in "${!forward_port_values[@]}"; do
        (( forward_index == 0 )) && continue
        forwarded_port=${forward_port_values[$forward_index]}
        netdev_config+=",hostfwd=tcp:127.0.0.1:${forwarded_port}-:${forwarded_port}"
    done
}
