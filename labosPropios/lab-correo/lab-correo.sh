#!/usr/bin/env bash
# =====================================================================
#  Lab de correo: SMTP + POP3 + MIME, estilo parcial, con corrector.
#  Correlo como TU usuario (no sudo). No necesita instalar servidores.
# =====================================================================
set -u
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABC="$HOME/lab-correo"; export LABC
say(){ printf '  %s\n' "$*"; }
hr(){ printf '%s\n' "----------------------------------------------------------------"; }

config(){
  mkdir -p "$LABC"
  echo; say "Configuración (se usa para corregir tus correos):"
  read -rp "    Tu legajo (ej 63051): " L
  read -rp "    Tu nombre y apellido (ej Juana Pérez): " N
  read -rp "    Tu cuenta ITBA (ej jperez@itba.edu.ar): " C
  [ -n "$L" ] && [ -n "$N" ] && [[ "$C" == *@* ]] || { say "datos incompletos, probá de nuevo"; exit 1; }
  python3 - "$L" "$N" "$C" <<'PY'
import json, os, sys
json.dump({"legajo": sys.argv[1], "nombre": sys.argv[2], "cuenta": sys.argv[3]},
          open(os.path.join(os.environ["LABC"], "config.json"), "w"), ensure_ascii=False)
PY
  say "guardado en $LABC/config.json"
}

running(){ pgrep -f "$LABC/servidor.py" >/dev/null; }

start(){
  cp -f "$SRC/servidor.py" "$SRC/corregir.py" "$LABC/"
  running || { nohup python3 "$LABC/servidor.py" >"$LABC/logs-servidor.txt" 2>&1 & }
  sleep 1
  running && say "servidores corriendo" || { say "no arrancó, mirá $LABC/logs-servidor.txt"; cat "$LABC/logs-servidor.txt"; }
}

up(){
  hr; say "LAB DE CORREO - levantando"; hr
  [ -f "$LABC/config.json" ] || config
  mkdir -p "$LABC/mail"
  cp -f "$SRC/corregir.py" "$LABC/"
  [ -n "$(ls -A "$LABC/mail" 2>/dev/null)" ] || python3 "$LABC/corregir.py" seed
  start
  L=$(python3 -c "import json;print(json.load(open('$LABC/config.json'))['legajo'])")
  hr
  say "SMTP recepción (MX) .... 127.0.0.1:2525   (mx1.protos.lab, dominios mail.protos.lab y mision.lab)"
  say "SMTP envío (submission)  127.0.0.1:2587   (requiere AUTH)"
  say "SMTP de empresa.lab .... lo descubrís por MX (ejercicio C8)"
  say "POP3 ................... 127.0.0.1:2110   usuario = contraseña = la dirección del buzón"
  say "DNS del lab ............ 127.0.0.1:5361 (UDP)"
  say "Tu buzón ............... ${L}@mail.protos.lab"
  say "Imagen para C5/C6 ...... $LABC/adjuntos/logo.png"
  hr
  say "Consignas: consignas.md   ·   Corregir: bash lab-correo.sh corregir C1"
  hr
}

case "${1:-}" in
  up) up ;;
  down) pkill -f "$LABC/servidor.py" && say "servidores apagados" || say "no estaba corriendo" ;;
  status) running && say "[on ] servidores (2525, 2587, 2110, 5361/udp)" || say "[off] servidores" ;;
  reset) pkill -f "$LABC/servidor.py"; rm -rf "$LABC/mail" "$LABC/logs"; mkdir -p "$LABC/mail"
         cp -f "$SRC/corregir.py" "$LABC/"; python3 "$LABC/corregir.py" seed; start; say "buzones vaciados y mensajes iniciales recreados" ;;
  config) config ;;
  corregir|pista|solucion) [ -n "${2:-}" ] || { say "uso: bash lab-correo.sh $1 C3"; exit 1; }
         cp -f "$SRC/corregir.py" "$LABC/"; python3 "$LABC/corregir.py" "$1" "$2" ;;
  log) f="$LABC/logs/${2:-smtp}.log"; [ -f "$f" ] && tail -n "${3:-40}" "$f" || say "todavía no hay $f" ;;
  *) cat <<'TXT'
uso: bash lab-correo.sh <comando>
  up                 levanta los servidores (la primera vez te pide legajo, nombre y cuenta)
  status | down      estado | apagar
  reset              vacía todos los buzones y recrea los mensajes iniciales
  config             cambiar legajo / nombre / cuenta
  corregir C3        corrige tu último correo de ese ejercicio
  pista C3           una pista corta
  solucion C1        respuestas del ejercicio de encontrar errores
  log [smtp|pop3]    lo último que vio el servidor (útil si algo no anda)
TXT
  ;;
esac
