#!/usr/bin/env bash
# Levanta LabProtos2025-2C desde cero.
set -uo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false          # evita el aviso "configured to build using Bake"
ROJO='\033[31m'; VERDE='\033[32m'; N='\033[0m'
die(){ printf "${ROJO}ERROR:${N} %s\n" "$1"; shift; for l in "$@"; do echo "   $l"; done; exit 1; }

# 1) Docker, plugin compose y daemon
command -v docker >/dev/null 2>&1 || die "no está instalado Docker." "sudo apt update && sudo apt install -y docker.io"
docker compose version >/dev/null 2>&1 || die "falta el plugin 'docker compose' (v2)." \
  "sudo apt update && sudo apt install -y docker-compose-v2"
docker info >/dev/null 2>&1 || die "no puedo hablar con el daemon de Docker." \
  "arrancalo:            sudo systemctl start docker" \
  "o usá sudo:           sudo make up" \
  "o sumate al grupo:    sudo usermod -aG docker \$USER   (y volvé a iniciar sesión)"

# 2) Las redes del parcial no pueden chocar con interfaces de tu VM
if command -v ip >/dev/null 2>&1; then
  for red in 192.168.50 192.168.100; do
    choque=$(ip -4 -o addr show 2>/dev/null | awk -v r="$red." '$4 ~ "^"r {print $2" "$4}' | grep -Ev '^(br-|docker)' || true)
    [ -n "$choque" ] && die "tu VM ya tiene una IP en la red $red.0/24, que usa el lab:" "$choque" \
      "quitásela mientras usás el lab, por ejemplo:" \
      "   sudo ip addr del $(echo "$choque" | awk '{print $2}' | head -1) dev $(echo "$choque" | awk '{print $1}' | head -1)"
  done
fi

# 3) Construir y levantar
echo "[*] Construyendo y levantando el lab (la primera vez tarda unos minutos)..."
docker compose up -d --build --remove-orphans || die "falló docker compose up" "mirá el detalle con:  make logs s=<servicio>"

# 4) Esperar a que todo esté healthy (que el contenedor diga "Started" no alcanza)
echo "[*] Esperando a que todos los servicios estén listos..."
ok=0
for i in $(seq 1 90); do
  pend=""
  for s in dns web parcial gateway alumno; do
    cid=$(docker compose ps -q "$s" 2>/dev/null)
    st=$( [ -n "$cid" ] && docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo "sin-crear")
    [ "$st" = healthy ] || pend="$pend $s($st)"
  done
  [ -z "$pend" ] && { ok=1; break; }
  sleep 2
done
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
[ "$ok" = 1 ] || die "estos servicios no quedaron listos:$pend" "mirá:  make logs s=<servicio>"

printf "\n${VERDE}Lab listo.${N}\n"
cat <<'MAP'

=====================  LabProtos2025-2C — Parcial 2Q2025  =====================
  Entrá a tu "VM" del parcial:            make ws
  Leé el enunciado:                       CONSIGNAS.md
  Autocorrector:                          make corregir   (o: make corregir ej=3)
  Volver al estado inicial del parcial:   make reset

  Red del lab (todo con IPs reales, nada de localhost):
    tu VM (alumno)        192.168.50.20  + una placa sin IP en 192.168.100.0/24
    gateway "A"           192.168.50.250
    protos.foo            192.168.50.80     parcial.protos.foo   192.168.50.90
    DNS del lab           192.168.50.53
===============================================================================
MAP
