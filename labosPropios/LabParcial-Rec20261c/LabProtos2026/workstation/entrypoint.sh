#!/bin/bash
set -e
# clave del alumno (para Ej4 y recu-2)
mkdir -p /root/.ssh
cp /opt/keys/id_ed25519 /root/.ssh/id_ed25519
cp /opt/keys/id_ed25519.pub /root/.ssh/id_ed25519.pub
chmod 700 /root/.ssh; chmod 600 /root/.ssh/id_ed25519; chmod 644 /root/.ssh/id_ed25519.pub
cp /opt/ssh_config /root/.ssh/config; chmod 600 /root/.ssh/config
echo "[*] workstation lista. Entra con:  docker compose exec workstation bash"
exec sleep infinity
