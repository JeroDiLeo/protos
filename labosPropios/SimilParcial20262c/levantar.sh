#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "[*] Construyendo y levantando el lab (la primera vez tarda, baja imagenes)..."
docker compose up -d --build
echo
echo "[*] Contenedores:"
docker compose ps
echo
cat <<MAP
========================  MAPA DE IPs  ========================
 Ej1  entry   HTTP     172.30.0.11:3126     (o 127.0.0.1:3126)
 Ej1  proxy   SOCKS5   172.30.0.12:1080     (o 127.0.0.1:1080)
 Ej1  secret  (oculto, solo via proxy -> secrets.ct.os)
 Ej2  host    nginx 80/81 + ssh 22
               172.30.0.20   (o 127.0.0.1:2280 / 2281 / 2222)
 Ej3  mail    SMTP/IMAP/POP3
               172.30.0.30   (o 127.0.0.1:2525 / 1143 / 1110)
 Ej4  http    172.30.0.40:8000   (o 127.0.0.1:8000)  -> backup.pcapng
 Ej4  bind    172.30.0.41:53     (o 127.0.0.1:5353)  -> tu DNS restaurado
 ---- EXTRAS (no estaban en el parcial, para practicar) -------
 Ej5  http    172.30.0.60:8000   (o 127.0.0.1:8010)  -> dhcp.pcapng
 Ej6  host    nginx 80 + ssh 22
               172.30.0.70        (o 127.0.0.1:2680 / 2622)
===============================================================
 Consignas:  CONSIGNAS.md        Soluciones:  solucion/SOLUCIONES.md
MAP
