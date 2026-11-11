#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false
ROJO='\033[31m'; VERDE='\033[32m'; N='\033[0m'
die(){ printf "${ROJO}ERROR:${N} %s\n" "$1"; shift; for l in "$@"; do echo "   $l"; done; exit 1; }
command -v docker >/dev/null 2>&1 || die "no está instalado Docker." "sudo apt install -y docker.io"
docker compose version >/dev/null 2>&1 || die "falta el plugin docker compose (v2)." "sudo apt install -y docker-compose-v2"
docker info >/dev/null 2>&1 || die "el daemon de Docker no responde." "sudo systemctl start docker   (o corré con sudo)"
if command -v ip >/dev/null 2>&1; then
  ch=$(ip -4 -o addr show 2>/dev/null | awk '$4 ~ /^192\.168\.60\./{print $2" "$4}' | grep -Ev '^(br-|docker)' || true)
  [ -n "$ch" ] && die "tu VM ya tiene una IP en 192.168.60.0/24, que usa el lab:" "$ch" "quitásela mientras usás el lab."
fi
echo "[*] Construyendo y levantando el lab (la 1ra vez tarda)..."
docker compose up -d --build --remove-orphans || die "falló docker compose up" "mirá: make logs s=<servicio>"
echo "[*] Esperando a que los servicios estén listos..."
ok=0
for i in $(seq 1 90); do
  pend=""
  for s in $(docker compose config --services); do
    cid=$(docker compose ps -q "$s" 2>/dev/null)
    st=$( [ -n "$cid" ] && docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo sin-crear)
    [ "$st" = healthy ] || [ "$st" = running ] || pend="$pend $s($st)"
  done
  [ -z "$pend" ] && { ok=1; break; }; sleep 2
done
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
[ "$ok" = 1 ] || die "estos servicios no quedaron listos:$pend" "mirá: make logs s=<servicio>"
printf "\n${VERDE}Lab listo.${N}  Entrá con:  make ws     ·     Enunciado:  CONSIGNAS.md\n"
