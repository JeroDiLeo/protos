#!/usr/bin/env bash
# Autocorrector del LabProtos2025-2C.
# Revisa lo que configuraste DENTRO del contenedor alumno y te dice qué está
# bien y qué falta, con una pista (sin darte la respuesta).
#   ./corregir.sh          -> todos los ejercicios
#   ./corregir.sh 3        -> solo el Ejercicio III   (1 | 2 | 3 | 4 | 4b)
set -uo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false

if ! docker compose ps --status running --services 2>/dev/null | grep -qx alumno; then
  echo "El lab no está levantado. Corré primero:  make up"; exit 1
fi

docker compose exec -T alumno bash -s -- "${1:-all}" <<'INSIDE'
EJ="$1"
G='\033[32m'; R='\033[31m'; Y='\033[33m'; B='\033[1m'; N='\033[0m'
P=0; T=0
ok(){  printf "  ${G}✔${N} %s\n" "$1"; P=$((P+1)); T=$((T+1)); }
bad(){ printf "  ${R}✘${N} %s\n" "$1"; [ -n "${2:-}" ] && printf "      ${Y}pista:${N} %s\n" "$2"; T=$((T+1)); }
title(){ printf "\n${B}%s${N}\n" "$1"; }

# ----------------------------------------------------------------- Ej I
ej1(){
  title "Ejercicio I — servidor DHCP (192.168.100.0/24)"
  IF=""
  for i in $(ip -o link show | awk -F': ' '{print $2}' | cut -d@ -f1); do
    [ "$i" = lo ] && continue
    ip -4 addr show dev "$i" | grep -q '192\.168\.50\.' && continue
    IF=$i; break
  done
  if [ -z "$IF" ]; then bad "no encuentro la interfaz de la red interna"; return; fi
  ip -4 addr show dev "$IF" | grep -q 'inet 192\.168\.100\.' \
    && ok "la interfaz interna ($IF) tiene una IP en 192.168.100.0/24" \
    || bad "la interfaz interna ($IF) no tiene IPv4 en 192.168.100.0/24" "el servidor DHCP necesita una IP propia dentro de la subred que sirve"
  grep -Eq "^INTERFACESv4=\"?$IF\"?\s*$" /etc/default/isc-dhcp-server \
    && ok "INTERFACESv4 apunta a $IF" \
    || bad "INTERFACESv4 no apunta a la interfaz interna ($IF)" "/etc/default/isc-dhcp-server"
  if ! grep -Eq '^[[:space:]]*subnet[[:space:]]+192\.168\.100\.0[[:space:]]+netmask[[:space:]]+255\.255\.255\.0' /etc/dhcp/dhcpd.conf 2>/dev/null; then
    bad "dhcpd.conf no declara la subnet 192.168.100.0/24" "/etc/dhcp/dhcpd.conf"
  elif dhcpd -t -4 -cf /etc/dhcp/dhcpd.conf >/dev/null 2>&1; then
    ok "dhcpd.conf declara 192.168.100.0/24 y no tiene errores"
  else
    bad "dhcpd.conf tiene errores" "sudo dhcpd -t -4 -cf /etc/dhcp/dhcpd.conf"
  fi
  r=$(grep -E '^[[:space:]]*range[[:space:]]' /etc/dhcp/dhcpd.conf 2>/dev/null | head -1 | tr -d ';')
  a=$(echo $r | awk '{print $2}'); b=$(echo $r | awk '{print $3}')
  [ "$a" = 192.168.100.10 ] && [ "$b" = 192.168.100.200 ] \
    && ok "range 192.168.100.10 - 192.168.100.200" \
    || bad "el range es '${a:-?} - ${b:-?}'" "el enunciado pide asignar el rango 10-200"
  if ! systemctl is-active isc-dhcp-server >/dev/null 2>&1; then
    bad "isc-dhcp-server no está corriendo" "sudo systemctl restart isc-dhcp-server  ·  journalctl -u isc-dhcp-server"
    return
  fi
  ok "isc-dhcp-server está corriendo"
  out=$(nmap --script broadcast-dhcp-discover --script-args "broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF" -e "$IF" 2>/dev/null)
  ip=$(echo "$out" | awk '/IP Offered/{print $NF; exit}')
  if [ -z "$ip" ]; then
    bad "un cliente común (AA:BB:CC:DD:EE:FF) no recibe ninguna oferta"
  else
    n=${ip##*.}
    { [ "${ip%.*}" = 192.168.100 ] && [ "$n" -ge 10 ] && [ "$n" -le 200 ] && [ "$n" != 8 ]; } \
      && ok "un cliente común recibe $ip" \
      || bad "un cliente común recibe $ip" "tiene que salir del rango 10-200"
  fi
  echo "$out" | grep -q "Domain Name Server: 8.8.8.8, 8.8.4.4" \
    && ok "los clientes reciben DNS 8.8.8.8 y 8.8.4.4" \
    || bad "los DNS ofrecidos no son 8.8.8.8 y 8.8.4.4" "mirá la opción de servidores de nombres (ojo con el plural)"
  imp=$(nmap --script broadcast-dhcp-discover --script-args "broadcast-dhcp-discover.mac=08:00:27:AE:C8:6A" -e "$IF" 2>/dev/null | awk '/IP Offered/{print $NF; exit}')
  [ "$imp" = 192.168.100.8 ] \
    && ok "la impresora (08:00:27:AE:C8:6A) recibe 192.168.100.8" \
    || bad "la impresora recibe '${imp:-nada}'" "una reserva por MAC dentro de la subnet"
}

# ----------------------------------------------------------------- Ej II
ej2(){
  title "Ejercicio II — servidor detrás del gateway 192.168.50.250"
  ip route | grep -Eq '^10\.0\.0\.0/24 via 192\.168\.50\.250' \
    && ok "hay ruta a 10.0.0.0/24 vía 192.168.50.250" \
    || bad "no hay ruta a 10.0.0.0/24 por el gateway" "tu VM no conoce esa red: hay que decirle por dónde ir"
  S=$(echo MTAuMC4wLjEzNw== | base64 -d)
  curl -s -m 5 "http://$S:8080/" 2>/dev/null | grep -q "Servidor encontrado" \
    && ok "llegás por HTTP al servidor de la red 10.0.0.0/24" \
    || bad "todavía no llegás por HTTP al servidor" "descubrí hosts y puertos con nmap"
  traceroute -n -q1 -w1 -m3 "$S" 2>/dev/null | grep -q "192.168.50.250" \
    && ok "el camino pasa por el router 192.168.50.250" \
    || bad "traceroute no muestra el paso por el gateway"
}

# ----------------------------------------------------------------- Ej III
ej3(){
  title "Ejercicio III — zona it.itba.edu.ar en BIND9"
  Z=/etc/bind/db.it.itba.edu.ar
  named-checkzone it.itba.edu.ar "$Z" >/dev/null 2>&1 \
    && ok "named-checkzone: la zona carga sin errores" \
    || { bad "la zona de $Z no carga" "named-checkzone it.itba.edu.ar $Z"; return; }
  systemctl is-active bind9 >/dev/null 2>&1 || { bad "bind9 no está corriendo" "sudo systemctl restart bind9"; return; }
  q(){ dig @127.0.0.1 +norec +short "$@" 2>/dev/null; }
  soa=$(q it.itba.edu.ar SOA)
  [ -n "$soa" ] || { bad "BIND no está sirviendo la zona corregida" "¿recargaste bind9 después de corregir?"; return; }
  dig @127.0.0.1 it.itba.edu.ar SOA 2>/dev/null | grep -Eq 'flags:[a-z ]* aa' \
    && ok "las respuestas son autoritativas (flag aa)" || bad "las respuestas no son autoritativas"
  [ "$(q pampero.it.itba.edu.ar A)" = 192.168.70.10 ] \
    && ok "pampero.it.itba.edu.ar -> 192.168.70.10" || bad "pampero.it.itba.edu.ar no resuelve bien"
  [ "$(q ns1.it.itba.edu.ar A)" = 192.168.70.1 ] \
    && ok "ns1.it.itba.edu.ar -> 192.168.70.1" \
    || bad "ns1.it.itba.edu.ar no resuelve" "¿qué pasa con un nombre sin punto final dentro de la zona?"
  w=$(q www.it.itba.edu.ar CNAME)
  if [ "$w" = pampero.it.itba.edu.ar. ]; then ok "www es CNAME de pampero"
  elif [ "$(q www.it.itba.edu.ar A | tail -1)" = 192.168.70.10 ]; then ok "www resuelve a 192.168.70.10 (como alias lo esperable es CNAME)"
  else bad "www.it.itba.edu.ar no resuelve" "un registro A no puede apuntar a un nombre"; fi
  [ "$(q correo.it.itba.edu.ar CNAME)" = pampero.it.itba.edu.ar. ] \
    && ok "correo es CNAME de pampero" || bad "correo.it.itba.edu.ar no es CNAME de pampero"
  mx=$(q it.itba.edu.ar MX | awk '{print $2}' | head -1)
  if [ -n "$mx" ] && [ -n "$(q "$mx" A)" ]; then ok "el MX ($mx) tiene registro A"
  else bad "el MX apunta a '${mx:-nada}', que no tiene dirección" "un MX tiene que apuntar a un host que exista"; fi
  set -- $soa
  [ "$2" = admin.it.itba.edu.ar. ] \
    && ok "contacto del SOA: admin.it.itba.edu.ar." || bad "contacto del SOA: '$2'" "en el SOA el mail no se escribe con @"
  [ "$3" -gt 2025060500 ] 2>/dev/null \
    && ok "serial incrementado ($3)" || bad "el serial no aumentó ($3)" "los secundarios solo transfieren si el serial sube"
  if [ "$4" -lt 604800 ] && [ "$5" -lt 86400 ] && [ "$7" -lt 604800 ]; then ok "refresh/retry/negative TTL más bajos (propagación rápida)"
  else bad "refresh/retry/negative TTL siguen altos ($4 / $5 / $7)" "para que el cambio se propague rápido"; fi
  ttl=$(dig @127.0.0.1 +norec +noall +answer pampero.it.itba.edu.ar A 2>/dev/null | awk '{print $2}')
  [ -n "$ttl" ] && [ "$ttl" -lt 604800 ] \
    && ok "TTL de los registros reducido ($ttl s)" || bad "el TTL sigue en ${ttl:-?} s" "\$TTL"
}

# ----------------------------------------------------------------- Ej IV
check_url(){  # $1 = url
  local url=$1 body code rc
  body=$(curl -s -m 6 "$url" 2>/dev/null); rc=$?
  case $rc in
    0) ;;
    6)  bad "curl $url: no resuelve el nombre" "¿cómo hace tu VM para saber la IP de ese nombre?"; return ;;
    7)  bad "curl $url: nadie escucha en ese puerto" "¿nginx está escuchando ahí?"; return ;;
    35) bad "curl $url: falla el handshake TLS" "revisá ssl_certificate / ssl_certificate_key"; return ;;
    60) bad "curl $url: curl no confía en el certificado (error 60)" "curl sin opciones exige que el certificado sea de confianza para el sistema"; return ;;
    51) bad "curl $url: el certificado no es para ese nombre" "CN / subjectAltName"; return ;;
    *)  bad "curl $url falla (código $rc)"; return ;;
  esac
  code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' "$url")
  case $code in 3*) bad "$url responde $code (redirección)" "no se debe ver modificada la URL"; return ;; esac
  if echo "$body" | grep -q "Contenido servido por parcial.protos.foo"; then ok "curl $url sirve el contenido de parcial.protos.foo"
  elif echo "$body" | grep -q "^What?"; then bad "$url devuelve 'What?'" "llegás al backend, pero el backend elige el sitio por el header Host"
  else bad "$url no devuelve el contenido de parcial.protos.foo" "¿cayó en otro server de nginx?"; fi
}
ej4(){
  title "Ejercicio IV — https://seguro.protos.foo"
  check_url https://seguro.protos.foo
}
ej4b(){
  title "Ejercicio IV-bis (extra, versión del apunte) — http://publico.protos.foo"
  check_url http://publico.protos.foo
}

case "$EJ" in
  1) ej1 ;; 2) ej2 ;; 3) ej3 ;; 4) ej4 ;; 4b) ej4b ;;
  all) ej1; ej2; ej3; ej4; ej4b ;;
  *) echo "uso: corregir.sh [1|2|3|4|4b]"; exit 1 ;;
esac
printf "\n${B}Resultado: %d/%d chequeos OK${N}\n" "$P" "$T"
INSIDE
