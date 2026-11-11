#!/bin/bash
# Workstation del alumno: arranca en el mismo estado que la VM del parcial.

# 1) DNS del lab (sin el DNS embebido de Docker: los nombres de contenedores no resuelven)
printf 'nameserver 192.168.50.53\noptions timeout:2 attempts:2\n' > /etc/resolv.conf

# 2) Ej I: la placa de la red 192.168.100.0/24 arranca SIN IPv4,
#    como una "Internal Network" recien agregada en VirtualBox.
LAN_IF=$(ip -o -4 addr show | awk '$4 ~ /^192\.168\.50\./ {print $2; exit}')
for ifc in $(ip -o -4 addr show | awk '$4 ~ /^192\.168\.100\./ {print $2}'); do
  ip addr flush dev "$ifc"; ip link set "$ifc" up
done
# la ruta por defecto sale por la LAN (192.168.50.1), como en la VM del parcial
ip route replace default via 192.168.50.1 dev "$LAN_IF"

# 3) Ej III: BIND arranca con la zona rota (se queja al cargarla)
systemctl start bind9 >/dev/null 2>&1

# 4) nginx recien instalado (sitio default activo)
systemctl start nginx >/dev/null 2>&1

touch /var/log/lab/dhcpd.log
exec sleep infinity
