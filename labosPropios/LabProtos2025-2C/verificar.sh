#!/usr/bin/env bash
# Verifica que la INFRAESTRUCTURA del lab funciona (no corrige tus ejercicios:
# para eso está 'make corregir'). No modifica nada de tu VM.
set -uo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false
ok(){ printf "  [\033[32mOK\033[0m] %s\n" "$1"; }
no(){ printf "  [\033[31m--\033[0m] %s\n" "$1"; FALLAS=1; }
FALLAS=0
A="docker compose exec -T alumno"

echo "== contenedores =="
for s in dns web parcial gateway alumno; do
  cid=$(docker compose ps -q $s 2>/dev/null)
  st=$( [ -n "$cid" ] && docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "no existe")
  [ "$st" = healthy ] && ok "$s healthy" || no "$s: $st"
done

echo "== DNS del lab (desde tu VM) =="
[ "$($A dig +short protos.foo)" = 192.168.50.80 ] && ok "protos.foo -> 192.168.50.80" || no "protos.foo no resuelve"
[ "$($A dig +short parcial.protos.foo)" = 192.168.50.90 ] && ok "parcial.protos.foo -> 192.168.50.90" || no "parcial.protos.foo no resuelve"

echo "== servicios de la cátedra =="
$A curl -s -m 4 http://protos.foo/zona | grep -q "IN SOA" && ok "http://protos.foo/zona disponible" || no "no se descarga la zona"
$A curl -s -m 4 http://parcial.protos.foo | grep -q "Contenido servido" && ok "http://parcial.protos.foo responde" || no "parcial.protos.foo no responde"
$A ping -c1 -W2 192.168.50.250 >/dev/null && ok "el gateway 192.168.50.250 responde ping" || no "el gateway no responde"
docker compose exec -T gateway /healthcheck.sh && ok "la red 10.0.0.0/24 detrás del gateway está arriba" || no "la red 10.0.0.0/24 no responde"

echo "== tu VM =="
n=$($A sh -c "ip -o link show | grep -vc ' lo:'")
[ "$n" -ge 2 ] && ok "tiene la placa extra para la red 192.168.100.0/24" || no "falta la placa de la red DHCP"
$A sh -c "command -v dhcpd named nginx nmap traceroute route openssl" >/dev/null && ok "herramientas del parcial instaladas" || no "faltan herramientas"

[ "$FALLAS" = 0 ] && printf "\n\033[32mLab funcional.\033[0m\n" || { printf "\n\033[31mHay problemas en el lab.\033[0m Mirá: make logs s=<servicio>\n"; exit 1; }
