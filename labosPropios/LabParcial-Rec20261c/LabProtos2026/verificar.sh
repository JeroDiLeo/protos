#!/usr/bin/env bash
# Resuelve cada ejercicio desde el lado del alumno (dentro del workstation)
# para confirmar que la infraestructura responde. No reemplaza tu practica:
# es solo la prueba de que el lab esta funcional.
set -uo pipefail
cd "$(dirname "$0")"
WS="docker compose exec -T workstation"
LEGAJO="${LEGAJO:-62815}"
ok(){ printf "  [\033[32mOK\033[0m] %s\n" "$1"; }
no(){ printf "  [\033[31m--\033[0m] %s\n" "$1"; }

echo "== Ej1 : datos DNS para armar la zona BIND =="
$WS dig +short A bar.protos.foo            | grep -q "123.123.123.123" && ok "A bar.protos.foo = 123.123.123.123" || no "no resuelve bar.protos.foo"
$WS dig +short MX mail.protos.foo          | grep -q "mx1.protos.foo" && ok "MX mail.protos.foo visibles (mx1/mx2)" || no "no resuelven los MX"

echo "== Ej2 : metadata (403 sin header, JSON con header) =="
$WS curl -s -o /dev/null -w '%{http_code}' http://metadata.protos.foo | grep -q 403 && ok "403 sin el header Metadata" || no "no da 403 sin header"
$WS curl -s -H 'Metadata: true' http://metadata.protos.foo | grep -q "superdupersecrettoken" && ok "JSON con Metadata: true" || no "no devuelve el JSON con el header"

echo "== Ej3 : HTTP acumulativo via SOCKS5 =="
$WS curl -s -x socks5h://proxy.protos.foo:1080 \
     -XPOST -H "X-legajo:$LEGAJO" -H "accept-language:es" \
     -H "content-type:application/json" -d '{"fix":"yes"}' -u admin:admin \
     http://ejercicio3.protos.foo:3126/debugger | grep -q "aprobado" \
     && ok "cadena completa -> APROBADO (via proxy)" || no "no llegue al aprobado via proxy"
# y que NO sea accesible sin proxy:
$WS bash -c "curl -s -m3 http://ejercicio3.protos.foo:3126/ >/dev/null 2>&1" \
     && no "ej3 es accesible SIN proxy (deberia fallar)" || ok "ej3 NO accesible sin proxy (correcto)"

echo "== Ej4 : pampero accesible por SSH + archivo que late =="
$WS ssh -o ConnectTimeout=5 alumno@pampero.itba.edu.ar 'test -f /tmp/parcial-20261 && echo yes' 2>/dev/null | grep -q yes \
     && ok "login SSH por clave + /tmp/parcial-20261 existe" || no "no pude entrar a pampero o falta el archivo"

echo "== Ej5 / recu-1 : SMTP + POP3 =="
$WS bash -c "printf 'EHLO ws\r\nMAIL FROM:<a@itba.edu.ar>\r\nRCPT TO:<$LEGAJO@mail.sebikul.com>\r\nDATA\r\nSubject: test\r\n\r\nhola\r\n.\r\nQUIT\r\n' | nc -C -w3 mail.sebikul.com 25" | grep -q "message queued" \
     && ok "SMTP acepto el mail (mail.sebikul.com:25)" || no "SMTP no acepto el mail"
$WS bash -c "printf 'USER $LEGAJO@mail.sebikul.com\r\nPASS x\r\nSTAT\r\nQUIT\r\n' | nc -C -w3 mail.sebikul.com 110" | grep -q "+OK 1" \
     && ok "POP3 muestra el mail recibido" || no "POP3 no muestra el mail"

echo "== recu-2 : parcial.protos.foo (nmap: 22/80/8000) + login =="
$WS bash -c "nc -z -w2 parcial.protos.foo 22 && nc -z -w2 parcial.protos.foo 80 && nc -z -w2 parcial.protos.foo 8000" \
     && ok "puertos 22/80/8000 abiertos" || no "faltan puertos en parcial"
$WS bash -c "command -v sshpass >/dev/null && sshpass -p holamundo ssh -o StrictHostKeyChecking=no parcial@parcial.protos.foo true 2>/dev/null && echo ok" | grep -q ok \
     && ok "login parcial/holamundo" || echo "  [i] login con password: probalo a mano (ssh parcial@parcial.protos.foo, pass holamundo)"
