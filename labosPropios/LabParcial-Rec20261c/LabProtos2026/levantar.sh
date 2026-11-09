#!/usr/bin/env bash
# Levanta LabProtos2026 desde cero. Pensado para arrancar limpio sin tocar nada.
set -euo pipefail
cd "$(dirname "$0")"

# ---- 1) Chequear Docker y Docker Compose ANTES de arrancar ----
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: no esta instalado Docker."
  echo "  En Ubuntu:  sudo apt update && sudo apt install -y docker.io"
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: falta el plugin 'docker compose' (v2)."
  echo "  En Ubuntu con docker.io se resuelve instalando:"
  echo "      sudo apt update && sudo apt install -y docker-compose-v2"
  echo "  (y agrega tu usuario al grupo docker, o corre con sudo)."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: el daemon de Docker no responde."
  echo "  Arranca el servicio:  sudo systemctl start docker"
  echo "  o corre este script con sudo."
  exit 1
fi

echo "[*] Construyendo imagenes y levantando el lab (la 1ra vez tarda)..."
docker compose up -d --build

# ---- 2) Esperar a que TODOS los servicios con healthcheck esten healthy ----
echo "[*] Esperando a que los servicios esten listos..."
services_hc="dns mail metadata pampero parcial"
for i in $(seq 1 60); do
  all_ok=1
  for s in $services_hc; do
    cid=$(docker compose ps -q "$s" 2>/dev/null || true)
    [ -z "$cid" ] && { all_ok=0; break; }
    st=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo starting)
    [ "$st" = "healthy" ] || { all_ok=0; break; }
  done
  [ "$all_ok" = "1" ] && break
  sleep 2
done
if [ "${all_ok:-0}" != "1" ]; then
  echo "AVISO: algun servicio tardo en quedar healthy. Reviso con: docker compose ps"
fi

echo
echo "[*] Estado:"; docker compose ps
cat <<'MAP'

===========================  LabProtos2026  ===========================
 Trabajas DENTRO del workstation. Entra con:

     docker compose exec workstation bash

 Desde ahi todo resuelve por nombre a IPs reales (nada de localhost):

   Ej1  BIND/DNS      dig bar.protos.foo / dig MX mail.protos.foo
   Ej2  nginx proxy   metadata.protos.foo            (172.28.0.20)
   Ej3  HTTP+SOCKS5   ejercicio3.protos.foo:3126 via proxy.protos.foo:1080
   Ej4  tunel SSH     pampero.itba.edu.ar  (user: alumno)
   Ej5  SMTP/POP3     mail.sebikul.com : 25 / 110
   recu-1  SMTP/POP3  mx1.protos.foo : 25   (POP3 en mail.protos.foo:110)
   recu-2  SSH persist parcial.protos.foo  (user: parcial / holamundo)

 Consignas:  CONSIGNAS.md     Soluciones:  solucion/SOLUCIONES.md
 Chequeo:    ./verificar.sh
=======================================================================
MAP
