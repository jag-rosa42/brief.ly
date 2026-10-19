"""Write cloud-init user-data and meta-data for one VM."""

import json
import os
import sys

(
    seed_dir,
    username,
    hostname,
    instance_id,
    public_key,
    architecture,
    docker_engine_version,
    docker_compose_version,
    docker_buildx_version,
    containerd_version,
) = sys.argv[1:]
docker_architecture = {"amd64": "amd64", "arm64": "arm64"}[architecture]
docker_source = "\n".join([
    "Types: deb",
    "URIs: https://download.docker.com/linux/ubuntu",
    "Suites: noble",
    "Components: stable",
    f"Architectures: {docker_architecture}",
    "Signed-By: /etc/apt/keyrings/docker.asc",
    "",
])
runcmd = [
    ["install", "-m", "0755", "-d", "/etc/apt/keyrings"],
    ["curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg", "-o", "/etc/apt/keyrings/docker.asc"],
    ["chmod", "a+r", "/etc/apt/keyrings/docker.asc"],
    ["apt-get", "update"],
    [
        "env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y",
        f"docker-ce={docker_engine_version}",
        f"docker-ce-cli={docker_engine_version}",
        f"containerd.io={containerd_version}",
        f"docker-buildx-plugin={docker_buildx_version}",
        f"docker-compose-plugin={docker_compose_version}",
    ],
    ["systemctl", "enable", "--now", "docker"],
    ["usermod", "-aG", "docker", username],
]
cloud_config = "\n".join([
    "#cloud-config",
    f"hostname: {json.dumps(hostname)}",
    "manage_etc_hosts: true",
    "ssh_pwauth: false",
    "disable_root: true",
    "ssh_deletekeys: true",
    "ssh_genkeytypes: [ed25519]",
    "users:",
    f"  - name: {username}",
    "    groups: [adm, sudo]",
    "    shell: /bin/bash",
    '    sudo: "ALL=(ALL) NOPASSWD:ALL"',
    "    lock_passwd: true",
    "    ssh_authorized_keys:",
    f"      - {json.dumps(public_key)}",
    "packages:",
    "  - openssh-server",
    "  - ca-certificates",
    "  - curl",
    "  - make",
    "package_update: true",
    "write_files:",
    "  - path: /etc/apt/sources.list.d/docker.sources",
    "    permissions: '0644'",
    f"    content: {json.dumps(docker_source)}",
    "runcmd:",
    *[f"  - {json.dumps(command)}" for command in runcmd],
    "",
])
files = {
    "user-data": cloud_config,
    "meta-data": f"instance-id: {instance_id}\nlocal-hostname: {hostname}\n",
}
for name, contents in files.items():
    path = os.path.join(seed_dir, name)
    with open(path, "w", encoding="utf-8") as stream:
        stream.write(contents)
    os.chmod(path, 0o600)
