#!/usr/bin/env bash
# Autocorrector del LabRecu2026. Revisa lo que hiciste DENTRO de la VM alumno.
#   ./corregir.sh            -> todos
#   ./corregir.sh 3          -> solo el Ejercicio 3   (1 | 2 | 2b | 3 | 4)
#   LEG=99999 ./corregir.sh 1   -> usar otro legajo para el Ej1 (default 62815)
set -uo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false
if ! docker compose ps --status running --services 2>/dev/null | grep -qx alumno; then
  echo "El lab no está levantado. Corré:  make up"; exit 1
fi
docker compose exec -T -e LEG="${LEG:-62815}" alumno bash -s -- "${1:-all}" <<'INSIDE'
EJ="$1"; LEG="${LEG:-62815}"
G='\033[32m'; R='\033[31m'; Y='\033[33m'; B='\033[1m'; N='\033[0m'
P=0; T=0
ok(){  printf "  ${G}✔${N} %s\n" "$1"; P=$((P+1)); T=$((T+1)); }
bad(){ printf "  ${R}✘${N} %s\n" "$1"; [ -n "${2:-}" ] && printf "      ${Y}pista:${N} %s\n" "$2"; T=$((T+1)); }
title(){ printf "\n${B}%s${N}\n" "$1"; }

pop3(){  # $1.. comandos POP3 -> imprime la sesion
  { for c in "$@"; do printf '%s\r\n' "$c"; done; sleep 0.4; } | nc -C -w4 mail.protos.foo 110 2>/dev/null
}

ej1(){
  title "Ejercicio 1 — correo a ${LEG}@mail.protos.foo (POP3)"
  U="${LEG}@mail.protos.foo"
  stat=$(pop3 "USER $U" "PASS $U" "STAT" "QUIT" | awk '/^\+OK [0-9]/{print $2; exit}')
  if [ -z "$stat" ] || [ "$stat" = 0 ]; then
    bad "no hay ningún correo en la casilla $U" "¿lo entregaste a esa dirección exacta? ¿cerraste el DATA con un punto solo?"; return
  fi
  ok "hay $stat correo(s) en la casilla $U"
  msg=$(pop3 "USER $U" "PASS $U" "RETR $stat" "QUIT")
  echo "$msg" | grep -qi '^X-Parcial:' && ok "tiene el header X-Parcial" || bad "falta el header X-Parcial"
  echo "$msg" | grep -qi '^Subject:' && ok "tiene Subject" || bad "falta el Subject"
  echo "$msg" | grep -qiE '^From:.*itba' && ok "el From usa una cuenta del ITBA" || bad "el From no parece una cuenta del ITBA" "nombre, apellido y cuenta ITBA"
  if echo "$msg" | grep -qi 'Content-Transfer-Encoding:[[:space:]]*base64'; then
    ok "el cuerpo va en base64 (lo lee un MUA sin quoted-printable)"
  elif echo "$msg" | grep -qi 'quoted-printable'; then
    bad "el cuerpo va en quoted-printable" "el enunciado pide que lo pueda leer un MUA que NO soporte quoted-printable"
  else
    bad "no se ve una codificación de transferencia explícita" "Content-Transfer-Encoding: base64"
  fi
  # negrita: el cuerpo decodificado deberia marcar la negrita
  b64=$(echo "$msg" | awk 'BEGIN{h=1} /^\r?$/{h=0;next} h==0{print}' | tr -d '\r')
  dec=$(echo "$b64" | base64 -d 2>/dev/null)
  echo "$dec" | grep -q 'Hola mundo' && ok "el cuerpo dice 'Hola mundo'" || bad "no encuentro 'Hola mundo' en el cuerpo" "¿codificaste bien el cuerpo?"
  echo "$dec" | grep -qE '[*<].*[Hh]ola' && ok "el cuerpo marca la negrita" || bad "el cuerpo no marca la negrita" "en texto plano la negrita se marca con *asteriscos*"
}

ej2(){
  title "Ejercicio 2 — proxy local a metadata (metadata.local)"
  code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://metadata.protos.foo 2>/dev/null)
  [ "$code" = 403 ] && ok "metadata.protos.foo da 403 sin el header (como debe)" || bad "metadata.protos.foo no responde 403 directo (code $code)"
  out=$(curl -s -m 5 http://metadata.local 2>/dev/null); rc=$?
  if [ $rc = 6 ]; then bad "curl http://metadata.local no resuelve" "¿cómo hace tu VM para saber la IP de metadata.local?"; return; fi
  if [ $rc = 7 ]; then bad "curl http://metadata.local: nadie escucha en el puerto 80" "¿arrancaste nginx con tu proxy?"; return; fi
  if echo "$out" | grep -q 's3cr3t-metadata-token'; then ok "curl http://metadata.local devuelve el JSON del endpoint"
  elif echo "$out" | grep -qi 'forbidden\|403'; then bad "metadata.local devuelve 403" "el proxy tiene que AGREGAR el header Metadata: true"
  else bad "metadata.local no devuelve el contenido del endpoint" "revisá el proxy_pass"; fi
}

ej2b(){
  title "Ejercicio 2-bis (extra) — negociación de contenido con curl"
  base=http://ejercicio2.protos.foo:8080/foo/
  curl -s "$base" -H "Accept: text/plain" -H "Accept-Language: es" | grep -q 'texto plano y en espanol' \
    && ok "el endpoint entrega text/plain en español con los Accept correctos" \
    || bad "el endpoint no respondió la representación esperada" "mirá el Accept y el Accept-Language"
  code=$(curl -s -o /dev/null -w '%{http_code}' "$base" -H "Accept: text/plain")
  [ "$code" = 406 ] && ok "sin pedir idioma devuelve 406 (negociación real)" || bad "sin Accept-Language debería dar 406 (dio $code)"
  printf "      ${Y}nota:${N} este ejercicio no deja nada configurado; se resuelve con el curl correcto.\n"
}

ej3(){
  title "Ejercicio 3 — zona recu.protos.foo en BIND9"
  Z=/etc/bind/db.recu.protos.foo
  [ -f "$Z" ] || Z=$(ls /etc/bind/db.recu* 2>/dev/null | head -1)
  if [ -z "${Z:-}" ] || [ ! -f "$Z" ]; then bad "no encuentro el archivo de zona de recu.protos.foo" "/etc/bind/db.recu.protos.foo"; return; fi
  named-checkzone recu.protos.foo "$Z" >/dev/null 2>&1 && ok "named-checkzone: la zona carga sin errores" || { bad "la zona no carga" "named-checkzone recu.protos.foo $Z"; return; }
  systemctl is-active bind9 >/dev/null 2>&1 || { bad "bind9 no está corriendo" "sudo systemctl start bind9"; return; }
  q(){ dig @127.0.0.1 +norec +short "$@" 2>/dev/null; }
  [ -n "$(q recu.protos.foo SOA)" ] || { bad "BIND no sirve la zona" "¿recargaste bind9?"; return; }
  dig @127.0.0.1 recu.protos.foo SOA 2>/dev/null | grep -Eq 'flags:[a-z ]* aa' && ok "respuestas autoritativas (flag aa)" || bad "las respuestas no son autoritativas"
  [ "$(q recu.protos.foo A)" = 93.184.216.34 ] && ok "A de recu.protos.foo = IP de bar.protos.foo" || bad "el A no apunta a la IP de bar.protos.foo" "resolvé bar.protos.foo con dig y copiá esa IP"
  ttl=$(dig @127.0.0.1 +norec +noall +answer recu.protos.foo A 2>/dev/null | awk '{print $2; exit}')
  [ "$ttl" = 3600 ] && ok "el A tiene TTL de 1 hora (3600)" || bad "el A tiene TTL ${ttl:-?}, no 3600" "validez de 1 hora"
  c=$(q www.recu.protos.foo CNAME)
  [ "$c" = recu.protos.foo. ] && ok "www es CNAME a la raíz de la zona" || bad "www no es CNAME a la raíz" "un CNAME apuntando a recu.protos.foo."
  cttl=$(dig @127.0.0.1 +norec +noall +answer www.recu.protos.foo CNAME 2>/dev/null | awk '{print $2; exit}')
  [ "$cttl" = 1209600 ] && ok "el CNAME tiene TTL de 2 semanas (1209600)" || bad "el CNAME tiene TTL ${cttl:-?}, no 1209600" "validez de 2 semanas"
  mx=$(q recu.protos.foo MX | sort)
  echo "$mx" | grep -q '10 mx1.protos.foo.' && echo "$mx" | grep -q '20 mx2.protos.foo.' \
    && ok "los MX son los mismos que mail.protos.foo (orden incluido)" \
    || bad "los MX no coinciden con los de mail.protos.foo" "resolvé los MX de mail.protos.foo y copialos con su prioridad"
  spf=$(q recu.protos.foo TXT)
  echo "$spf" | grep -q 'v=spf1' && echo "$spf" | grep -q '1.2.3.4' && echo "$spf" | grep -qE '[-~]all' \
    && ok "hay un TXT SPF que sólo autoriza a 1.2.3.4" \
    || bad "falta el registro SPF (o no restringe a 1.2.3.4)" "un TXT v=spf1 ip4:1.2.3.4 -all"
}

ej4(){
  title "Ejercicio 4 — persistencia de acceso SSH a parcial.protos.foo"
  if ! getent hosts parcial.protos.foo >/dev/null 2>&1; then bad "parcial.protos.foo no resuelve (¿está levantado el contenedor?)"; return; fi
  [ -f /root/.ssh/id_ed25519 ] || [ -f /root/.ssh/id_rsa ] && ok "tenés una clave SSH generada" || bad "no tenés una clave SSH" "ssh-keygen -t ed25519"
  out=$(ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=6 \
        -o PasswordAuthentication=no -o PreferredAuthentications=publickey \
        parcial@parcial.protos.foo 'echo OK-SIN-PASSWORD; id -un' 2>/dev/null)
  if echo "$out" | grep -q OK-SIN-PASSWORD; then
    ok "entrás por clave, SIN contraseña (persistencia lograda)"
    u=$(echo "$out" | tail -1); [ "$u" = parcial ] && ok "la sesión es del usuario parcial" || true
  else
    bad "todavía no entrás sin contraseña" "entrá una vez con la contraseña filtrada y dejá autorizada tu clave pública"
  fi
}

case "$EJ" in
  1) ej1 ;; 2) ej2 ;; 2b) ej2b ;; 3) ej3 ;; 4) ej4 ;;
  all) ej1; ej2; ej2b; ej3; ej4 ;;
  *) echo "uso: corregir.sh [1|2|2b|3|4]"; exit 1 ;;
esac
printf "\n${B}Resultado: %d/%d chequeos OK${N}\n" "$P" "$T"
INSIDE
