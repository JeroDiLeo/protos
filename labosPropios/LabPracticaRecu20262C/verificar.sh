#!/usr/bin/env bash
# Verifica que la INFRAESTRUCTURA del lab responde (no corrige tus ejercicios:
# para eso está 'make corregir'). No modifica nada de tu VM.
set -uo pipefail
cd "$(dirname "$0")"; export COMPOSE_BAKE=false
ok(){ printf "  [\033[32mOK\033[0m] %s\n" "$1"; }
no(){ printf "  [\033[31m--\033[0m] %s\n" "$1"; F=1; }
F=0; A="docker compose exec -T alumno"
echo "== contenedores =="
for s in $(docker compose config --services); do
  cid=$(docker compose ps -q $s 2>/dev/null)
  st=$( [ -n "$cid" ] && docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo "no existe")
  { [ "$st" = healthy ] || [ "$st" = running ]; } && ok "$s ($st)" || no "$s: $st"
done
echo "== DNS del lab =="
[ "$($A dig +short mail.protos.foo)" = 192.168.60.70 ] && ok "mail.protos.foo" || no "mail.protos.foo no resuelve"
[ "$($A dig +short A bar.protos.foo)" = 93.184.216.34 ] && ok "bar.protos.foo (dato Ej3)" || no "bar.protos.foo no resuelve"
echo "== servicios =="
$A bash -c 'printf "QUIT\r\n" | nc -C -w3 mail.protos.foo 25' | grep -q 220 && ok "SMTP mail.protos.foo:25" || no "SMTP no responde"
$A bash -c 'printf "QUIT\r\n" | nc -C -w3 mail.protos.foo 110' | grep -q +OK && ok "POP3 mail.protos.foo:110" || no "POP3 no responde"
$A curl -s -o /dev/null -w '%{http_code}' -H "Metadata: true" http://metadata.protos.foo | grep -q 200 && ok "metadata.protos.foo" || no "metadata no responde"
$A curl -s http://ejercicio2.protos.foo:8080/foo/ -H "Accept: text/plain" -H "Accept-Language: es" | grep -q espanol && ok "ejercicio2 (content negotiation)" || no "ejercicio2 no responde"
if $A getent hosts parcial.protos.foo >/dev/null 2>&1; then
  $A bash -c 'nc -z -w3 parcial.protos.foo 22' && ok "parcial.protos.foo:22 (SSH)" || no "SSH de parcial no responde"
else no "parcial.protos.foo no resuelve (contenedor SSH no levantado)"; fi
[ "$F" = 0 ] && printf "\n\033[32mLab funcional.\033[0m\n" || { printf "\n\033[31mHay problemas.\033[0m make logs s=<servicio>\n"; exit 1; }
