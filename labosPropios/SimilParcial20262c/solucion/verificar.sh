#!/bin/bash
# Verifica que los 4 ejercicios resuelven correctamente (usa las IP de contenedor).
# Corré esto DESPUES de haber resuelto el Ej4 (el resto anda apenas levantás el lab).
LEGAJO="${LEGAJO:-62345}"
ok(){ echo -e "  [\e[32mOK\e[0m] $1"; }
no(){ echo -e "  [\e[31m--\e[0m] $1"; }

echo "== Ej1 : HTTP + SOCKS5 =="
curl -s -D - http://172.30.0.11:3126/ -o /dev/null | grep -qi X-CTOS-Proxy \
  && ok "headers/pistas visibles con -v" || no "no veo los headers de pista"
curl -s --socks5-hostname 172.30.0.12:1080 http://secrets.ct.os/ | grep -q "FLAG{ej1" \
  && ok "tunel SOCKS5 -> secrets.ct.os" || no "no pude tunelizar al host oculto"

echo "== Ej2 : nginx + SSH =="
curl -s http://172.30.0.20/sec/ | grep -q "mykey" \
  && ok "listing de /sec/ abierto (se ve mykey + pista)" || no "no veo el listing de /sec/"
curl -s http://172.30.0.20/sec/mykey | grep -q "PRIVATE KEY" \
  && ok "clave privada expuesta por HTTP (:80)" || no "no pude bajar la clave"
curl -s -H "Host: secrethost" http://172.30.0.20:81/ | grep -q "FLAG{ej2" \
  && ok "panel interno via vhost :81" || no "no llegue al panel :81"
PW=$(curl -s -D - -o /dev/null -H "Host: secrethost" http://172.30.0.20:81/ \
       | awk -F': ' '/X-Passphrase-B64/{print $2}' | tr -d "\r" | base64 -d 2>/dev/null)
[ -n "$PW" ] && ok "passphrase recuperada por pistas: $PW" || no "no pude leer el header X-Passphrase-B64"
echo "  (login SSH a mano -> ssh -i mykey -p 2222 pepito@127.0.0.1 ; pass: la de arriba)"

echo "== Ej3 : SMTP + IMAP =="
printf 'a login %s %s\nb select INBOX\nc logout\n' "$LEGAJO" "$LEGAJO" \
  | nc -w3 172.30.0.30 143 2>/dev/null | grep -qi "EXISTS" \
  && ok "IMAP login + casilla con mensajes" || no "IMAP no respondio (revisá legajo en .env)"

echo "== Ej4 : DNS / bind9 =="
if command -v dig >/dev/null; then
  dig +short @172.30.0.41 protos.lab SOA | grep -q ns1 \
    && ok "SOA/zona cargada en bind9" || no "la zona no responde (restaurá named.conf.local + db.protos.lab)"
  dig +short @172.30.0.41 protos.lab TXT | grep -q "cachito hola" \
    && ok 'TXT "cachito hola" presente' || no 'falta el TXT "cachito hola"'
else
  no "no tenés dig instalado para verificar el Ej4"
fi

echo "== Ej5 (EXTRA) : DHCP =="
curl -s http://172.30.0.60:8000/dhcp.pcapng -o /tmp/_dhcp.pcapng 2>/dev/null \
  && [ -s /tmp/_dhcp.pcapng ] && ok "pcap DHCP descargable (analizalo en Wireshark)" \
  || no "no pude bajar el pcap de DHCP"

echo "== Ej6 (EXTRA) : passphrase en pcap =="
curl -s http://172.30.0.70/sec/ | grep -q "captura.pcapng" \
  && ok "captura.pcapng visible en /sec/" || no "no veo la captura en /sec/"
PW6=$(curl -s http://172.30.0.70/sec/captura.pcapng \
        | strings 2>/dev/null | grep -i "Authorization: Basic" \
        | awk '{print $3}' | tr -d "\r" | base64 -d 2>/dev/null)
[ -n "$PW6" ] && ok "passphrase recuperable del pcap: $PW6" \
  || no "no pude extraer el Basic auth del pcap (hacelo con Wireshark: Follow TCP Stream)"
echo "  (login SSH a mano -> ssh -i mykey -p 2622 pepito@127.0.0.1 ; pass: la de arriba)"
