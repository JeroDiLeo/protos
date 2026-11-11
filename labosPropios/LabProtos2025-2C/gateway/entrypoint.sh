#!/bin/bash
# Host "A": router entre la LAN (192.168.50.250) y la red 10.0.0.0/24.
# La red 10.0.0.0/24 vive adentro de este contenedor: el servidor oculto corre
# en su propio network namespace, conectado a A por un par veth.
set -e

# 1) namespace de red del servidor oculto
unshare -n sleep infinity &
SRV=$!
echo $SRV > /run/srv.pid
sleep 0.3

# 2) cable virtual A <-> servidor
ip link add eth1 type veth peer name srv0
ip link set srv0 netns $SRV
ip addr add 10.0.0.254/24 dev eth1
ip link set eth1 up

# 3) lado servidor: 10.0.0.137, ruta por defecto via A
nsenter -t $SRV -n sh -c '
  ip link set lo up
  ip link set srv0 name eth0
  ip addr add 10.0.0.137/24 dev eth0
  ip link set eth0 up
  ip route add default via 10.0.0.254
'

# 4) servicios expuestos por el servidor: ssh (22) y http (8080)
ssh-keygen -A >/dev/null; mkdir -p /run/sshd
nsenter -t $SRV -n /usr/sbin/sshd
nsenter -t $SRV -n nginx

echo "gateway A listo: 192.168.50.250 <-> 10.0.0.254 | servidor 10.0.0.137 (22, 8080)"
exec sleep infinity
